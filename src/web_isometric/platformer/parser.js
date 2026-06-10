// Misthollow platformer: MUD text -> typed game events.
// Regex tables extended from client2d.html; the single source of truth for
// which lines of telnet prose drive which animations and UI updates.
(() => {
  const MH = window.MH = window.MH || {};

  const HIT_TARGET = /^You (?:hit|slash|pierce|smite|blast|attack|pound|crush|whip|claw|sting|bite|kick|bash|cleave|backstab) (?:at )?([A-Za-z' -]+?)(?:\.|!| for| with| very| extremely| hard|$)/i;
  // full format: "Your <damage word> <verb>s <target>! [23 damage]" - damage
  // words can be multi-word ("barely scratch"), so anchor on the verb list
  const VERBS = 'hits|stings|whips|slashes|bites|bludgeons|crushes|pounds|claws|mauls|thrashes|pierces|blasts|punches|stabs|slices|cleaves|smashes';
  const HIT_DMG_FULL = new RegExp(`^Your .+? (?:${VERBS}) (.+?)! \\[(\\d+) damage\\]`, 'i');
  const HIT_DMG_COMPACT = /^You \w+ (.+?)\. \[(\d+)\]/i;
  // incoming: "a janitor's scratch hits you! [3 damage]"  compact: "a janitor hits you. [3]"
  const TAKEN_DMG_FULL = new RegExp(`^(.+?)'s .+? (?:${VERBS}) you! \\[(\\d+) damage\\]`, 'i');
  const TAKEN_DMG_COMPACT = /^(.+?) \w+s? you\. \[(\d+)\]/i;
  const EXP_GAIN = /You receive (\d+) experience/i;
  const MISS_TARGET = /^You miss ([A-Za-z' -]+?)(?:\.|!|$)/i;
  const TAKEN = /(?:hits?|slashes|pierces|smites|blasts|attacks|pounds|crushes|whips|claws|stings|bites|kicks|bashes|cleaves|backstabs) you\b/i;
  const MISSED_ME = /(?:misses) you\b/i;
  const MOB_DEATH = /^(.+?) is dead!|^You receive .* experience/i;
  const PLAYER_DEATH = /you are dead|you have been slain/i;
  const LEVEL_UP = /you gain a level|you have gained a level|you are now level/i;
  const MOVE_BLOCKED = /alas, you cannot go that way|the .* (?:is|seems to be) closed|seems to be locked|it'?s locked|you are too exhausted|no exit in that direction|you can'?t go that way|^only .+ may enter\.?$/i;
  const POSTURE_BLOCK = /you need to stand up first|you can'?t do that while (?:resting|sitting|sleeping)|you are asleep/i;
  const DOOR_OPENED = /^(?:You open|.* opens) (?:the )?(.+?)\.?$/i;
  const FLEE = /^You flee(?: (\w+))?|panic and (?:try to )?flee/i;
  const CHAT = /^(You say|You tell|You shout|You gossip|You chat|\w+ says?|\w+ tells you|\w+ shouts?|\w+ gossips?|\[\w+\])/i;
  const COMBAT_LINE = /you hit|you slash|you pierce|you smite|you blast|you miss|is dead!|you are fighting|hits you|slashes you|attacks you|misses you|parry|dodge|block/i;
  const HEAL = /you feel (?:better|much better|healthier)|heals you|your wounds/i;
  const CAST_START = /^You (?:begin casting|start to cast|utter the words)/i;
  const NOT_HERE = /they aren'?t here|you do not see that here|kill who/i;
  const SLEEP_LINE = /^You go to sleep|^You wake|^You stand up|^You sit down|^You rest/i;
  const GOLD_LINE = /you (?:get|receive|find) (\d+) (?:gold )?coins?/i;

  MH.parseLine = function parseLine(msg) {
    let line = typeof msg === 'string' ? msg : msg.line;
    const chunkLen = typeof msg === 'object' ? (msg.chunkLen || 99) : 99;
    // the MUD prompt has no trailing newline, so it glues to the next
    // message - strip it before matching
    line = line.replace(/^\s*\d+\/\d+hp.*?>\s*/i, '');
    if (!line.trim()) return;
    const bus = MH.bus;
    let m;

    if (PLAYER_DEATH.test(line)) { MH.setCombat(false); bus.emit('player.death', { line }); return; }
    if ((m = line.match(EXP_GAIN))) { bus.emit('player.exp', { amount: Number(m[1]), line }); /* fall through to MOB_DEATH below */ }
    if ((m = line.match(HIT_DMG_FULL)) || (m = line.match(HIT_DMG_COMPACT))) {
      MH.setCombat(true);
      bus.emit('combat.hit', { target: m[1].trim(), dmg: Number(m[2]), line });
      return;
    }
    if ((m = line.match(TAKEN_DMG_FULL)) || (m = line.match(TAKEN_DMG_COMPACT))) {
      MH.setCombat(true);
      bus.emit('combat.taken', { from: m[1].trim(), dmg: Number(m[2]), line });
      return;
    }
    if ((m = line.match(MOB_DEATH))) {
      bus.emit('mob.death', { name: (m[1] || '').trim(), line });
      MH.setCombat(false);
      MH.refreshState();
      return;
    }
    if (LEVEL_UP.test(line)) { bus.emit('level.up', { line }); MH.refreshState(); return; }
    if (MOVE_BLOCKED.test(line)) { bus.emit('move.blocked', { line }); return; }
    if (POSTURE_BLOCK.test(line)) {
      // movement is the most common cause: stand and retry transparently
      bus.emit('move.blocked', { line, posture: true });
      MH.sendCommand('stand', false);
      return;
    }
    if ((m = line.match(HIT_TARGET))) { MH.setCombat(true); bus.emit('combat.hit', { target: m[1].trim(), line }); return; }
    if ((m = line.match(MISS_TARGET))) { MH.setCombat(true); bus.emit('combat.miss', { target: m[1].trim(), line }); return; }
    // defensive skills: yours and theirs, each with its own event
    if ((m = line.match(/^You parry (.+?)'s attack/i))) { MH.setCombat(true); bus.emit('defense.parry', { from: m[1], line }); return; }
    if ((m = line.match(/^You dodge (?:(.+?)'s attack|the attack)/i))) { MH.setCombat(true); bus.emit('defense.dodge', { from: m[1] || '', line }); return; }
    if (/^You block the attack/i.test(line)) { MH.setCombat(true); bus.emit('defense.block', { line }); return; }
    if ((m = line.match(/^(.+?) parries your attack/i))) { MH.setCombat(true); bus.emit('attack.parried', { target: m[1], line }); return; }
    if ((m = line.match(/^(.+?) dodges (?:your attack|like a ghost|from the shadows)/i))) { MH.setCombat(true); bus.emit('attack.dodged', { target: m[1], line }); return; }
    if ((m = line.match(/^(.+?) blocks (?:your attack|the attack with)/i))) { MH.setCombat(true); bus.emit('attack.blocked', { target: m[1], line }); return; }
    if (MISSED_ME.test(line)) { MH.setCombat(true); bus.emit('combat.dodged', { line }); return; }
    if (TAKEN.test(line)) { MH.setCombat(true); bus.emit('combat.taken', { line }); return; }
    if (NOT_HERE.test(line)) { bus.emit('combat.notarget', { line }); return; }
    if ((m = line.match(/^You flee (\w+)!/i))) {
      MH.setCombat(false);
      bus.emit('combat.flee', { dir: m[1].toLowerCase(), line });
      return;
    }
    if (FLEE.test(line)) { MH.setCombat(false); bus.emit('combat.flee', { line }); return; }
    if (CAST_START.test(line)) { bus.emit('combat.cast', { line }); return; }
    if (HEAL.test(line)) { bus.emit('player.heal', { line }); return; }
    if ((m = line.match(GOLD_LINE))) { bus.emit('player.gold', { amount: Number(m[1]), line }); return; }
    if ((m = line.match(DOOR_OPENED))) { bus.emit('door.opened', { name: m[1], line }); MH.refreshState(); return; }
    if (SLEEP_LINE.test(line)) { bus.emit('player.posture', { line }); return; }
    if (CHAT.test(line)) { bus.emit('chat', { line }); return; }
    if (COMBAT_LINE.test(line)) { bus.emit('combat.misc', { line }); return; }
    // nothing matched: short standalone chunks are ambient narrative
    if (MH.state && MH.state.isLoggedIn && chunkLen <= 2) bus.emit('ambient.candidate', { line });
  };

  // wire the bus
  MH.bus.on('mud.line', MH.parseLine);
})();
