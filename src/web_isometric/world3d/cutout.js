// "See-through" walls and trees: anything between the camera and the hero, within a
// circle around the hero on screen, is dithered away. One shared set of uniforms;
// call cutout.update(camera, heroPosition) each frame and cutout.apply(material) once
// per occluder material (walls, trees, big props — not floors).
import * as THREE from 'three';

const uniforms = {
  uCutCenter: { value: new THREE.Vector2(0, 0) },  // hero in NDC
  uCutRadius: { value: 0.16 },                       // NDC units (height)
  uCutAspect: { value: 1 },
  uCutDepth: { value: 1e9 },                         // hero distance from camera
};
const _v = new THREE.Vector3();

export const cutout = {
  uniforms,
  update(camera, pos) {
    _v.copy(pos).setY(pos.y + 1.0).project(camera);
    uniforms.uCutCenter.value.set(_v.x, _v.y);
    uniforms.uCutAspect.value = camera.aspect;
    _v.copy(pos).setY(pos.y + 1.0).applyMatrix4(camera.matrixWorldInverse);
    uniforms.uCutDepth.value = -_v.z;
    // a constant hole size in world terms: shrink it as the camera pulls back
    uniforms.uCutRadius.value = THREE.MathUtils.clamp(4.2 / Math.max(1, -_v.z), 0.08, 0.3);
  },
  apply(material) {
    if (material.userData.cutout) return material;
    material.userData.cutout = true;
    const prev = material.onBeforeCompile;
    material.onBeforeCompile = (shader, r) => {
      if (prev) prev(shader, r);
      Object.assign(shader.uniforms, uniforms);
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', '#include <common>\nvarying vec4 vCutClip;')
        .replace('#include <project_vertex>', '#include <project_vertex>\nvCutClip = gl_Position;');
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <common>', `#include <common>
varying vec4 vCutClip;
uniform vec2 uCutCenter; uniform float uCutRadius; uniform float uCutAspect; uniform float uCutDepth;
float cutBayer(vec2 p) {
  vec2 q = mod(floor(p), 4.0);
  float i = q.x + q.y * 4.0;
  // 4x4 ordered dither thresholds
  if (i < 1.0) return 0.0/16.0; if (i < 2.0) return 8.0/16.0; if (i < 3.0) return 2.0/16.0; if (i < 4.0) return 10.0/16.0;
  if (i < 5.0) return 12.0/16.0; if (i < 6.0) return 4.0/16.0; if (i < 7.0) return 14.0/16.0; if (i < 8.0) return 6.0/16.0;
  if (i < 9.0) return 3.0/16.0; if (i < 10.0) return 11.0/16.0; if (i < 11.0) return 1.0/16.0; if (i < 12.0) return 9.0/16.0;
  if (i < 13.0) return 15.0/16.0; if (i < 14.0) return 7.0/16.0; if (i < 15.0) return 13.0/16.0; return 5.0/16.0;
}`)
        .replace('void main() {', `void main() {
  {
    vec2 ndc = vCutClip.xy / vCutClip.w;
    vec2 d = (ndc - uCutCenter) * vec2(uCutAspect, 1.0);
    float r = length(d) / uCutRadius;
    // only what stands in front of the hero (closer to the camera) is cut
    float front = smoothstep(0.6, 1.6, uCutDepth - vCutClip.w);
    float keep = mix(1.0, smoothstep(0.55, 1.0, r), front);
    if (keep < 0.999 && keep <= cutBayer(gl_FragCoord.xy)) discard;
  }`);
    };
    const prevKey = material.customProgramCacheKey ? material.customProgramCacheKey.bind(material) : () => '';
    material.customProgramCacheKey = () => prevKey() + '|cutout';
    material.needsUpdate = true;
    return material;
  },
};
