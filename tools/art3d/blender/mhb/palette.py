"""One small palette texture a model: a cell per named colour, each a ramp from light (top) to dark
(bottom) like the KayKit textures, so a body can be shaded along its height. Faces are coloured by
pointing their UVs into a cell (paint) or along its ramp (paint_ramp); the cell's edge is never
sampled, so mipmaps don't bleed one colour into the next."""
import bpy

CELL = 16


def _rgb(hexs):
    h = hexs.lstrip('#')
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


class Palette:
    def __init__(self, name, colours, light=1.18, dark=0.62):
        """colours: {key: '#rrggbb'} or {key: ['#top', '#mid', '#bottom']}."""
        self.name = name
        self.keys = list(colours)
        n = len(self.keys)
        self.cols = 1
        while self.cols * self.cols < n:
            self.cols *= 2
        self.rows = max(1, (n + self.cols - 1) // self.cols)
        w, h = self.cols * CELL, self.rows * CELL
        img = bpy.data.images.new(f'{name}_palette', w, h, alpha=False)
        px = [0.0] * (w * h * 4)
        for i, k in enumerate(self.keys):
            v = colours[k]
            if isinstance(v, str):
                base = _rgb(v)
                top = [min(1, c * light) for c in base]
                bot = [c * dark for c in base]
                ramp = [top, base, bot]
            else:
                ramp = [_rgb(x) for x in v]
            cx, cy = (i % self.cols) * CELL, (i // self.cols) * CELL
            for y in range(CELL):
                t = y / (CELL - 1)                 # image rows run bottom-up: y=0 is the dark end
                a, b, f = (ramp[1], ramp[0], (t - 0.5) * 2) if t >= 0.5 else (ramp[2], ramp[1], t * 2)
                c = [a[j] + (b[j] - a[j]) * f for j in range(3)]
                for x in range(CELL):
                    o = ((cy + y) * w + cx + x) * 4
                    px[o:o + 4] = [c[0], c[1], c[2], 1.0]
        img.pixels = px
        img.pack()
        self.image = img
        self.material = self._material()

    def _material(self):
        m = bpy.data.materials.new(f'{self.name}_mat')
        m.use_nodes = True
        nt = m.node_tree
        bsdf = nt.nodes.get('Principled BSDF')
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = self.image
        tex.interpolation = 'Closest'
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Roughness'].default_value = 0.85
        bsdf.inputs['Metallic'].default_value = 0.0
        return m

    def uv(self, key, t=0.5):
        """The UV of a colour, t from 0 (its dark end) to 1 (its light end), inside the cell."""
        i = self.keys.index(key)
        cx, cy = i % self.cols, i // self.cols
        u = (cx + 0.5) / self.cols
        tt = 0.15 + 0.7 * max(0.0, min(1.0, t))
        v = (cy + tt) / self.rows
        return (u, v)

    def _layer(self, me):
        return me.uv_layers.active or me.uv_layers.new(name='UVMap')

    def paint(self, obj, key, faces=None, t=0.5):
        """Every face (or the given face indices) one colour."""
        me = obj.data
        uvl = self._layer(me)
        uv = self.uv(key, t)
        want = None if faces is None else set(faces)
        for p in me.polygons:
            if want is not None and p.index not in want:
                continue
            for li in p.loop_indices:
                uvl.data[li].uv = uv
        self.apply(obj)

    def paint_ramp(self, obj, key, faces=None, lo=None, hi=None):
        """Faces coloured along the ramp by height: light on top, dark underneath."""
        me = obj.data
        uvl = self._layer(me)
        zs = [(obj.matrix_world @ v.co).z for v in me.vertices]
        lo = min(zs) if lo is None else lo
        hi = max(zs) if hi is None else hi
        span = max(1e-6, hi - lo)
        want = None if faces is None else set(faces)
        for p in me.polygons:
            if want is not None and p.index not in want:
                continue
            for li in p.loop_indices:
                vi = me.loops[li].vertex_index
                uvl.data[li].uv = self.uv(key, (zs[vi] - lo) / span)
        self.apply(obj)

    def apply(self, obj):
        if not obj.data.materials:
            obj.data.materials.append(self.material)
        else:
            obj.data.materials[0] = self.material
