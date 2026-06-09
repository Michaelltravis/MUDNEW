// Misthollow platformer: MUD text -> typed game events.
// Regex tables extended from client2d.html; the single source of truth for
// which lines of telnet prose drive which animations and UI updates.
(() => {
  const MH = window.MH = window.MH || {};

  const HIT_TARGET = /^You (?:hit|slash|pierce|smite|blast|attack|pound|crush|whip|claw|sting|bite|kick|bash|cleave|backstab) (?:at )?([A-Za-z' -]+?)(?:\.|!| for| with| very| extremely| hard|$)/i;
  const MISS_TARGET = /^You miss ([A-Za-z' -]+?)(?:\.|!|$)/i;
  const TAKEN = /(?:hits?|slashes|pierces|smites|blasts|attacks|pounds|crushes|whips|claws|stings|bites|kicks|bashes|cleaves|backstabs) you\b/i;
  const MISSED_ME = /(?:misses) you\b/i;
  const MOB_DEATH = /^(.+?) is dead!|^You receive .* experience/i;
  const PLAYER_DEATH = /you are dead|you have been slain/i;
  const LEVEL_UP = /you gain a level|you have gained a level|you are now level/i;
  const MOVE_BLOCKED = /alas, you cannot go that way|the .* (?:is|seems to be) closed|seems to be locked|it'?s locked|you are too exhausted|no exit in that direction|you can'?t go that way/i;
  const DOOR_OPENED = /^(?:You open|.* opens) (?:the )?(.+?)\.?$/i;
  const FLEE = /^You flee|panic, and attempt to flee/i;
  const CHAT = /^(You say|You tell|You shout|You gossip|You chat|\w+ says?|\w+ tells you|\w+ shouts?|\w+ gossips?|\[\w+\])/i;
  const COMBAT_LINE = /you hit|you slash|you pierce|you smite|you blast|you miss|is dead!|you are fighting|hits you|slashes you|attacks you|misses you|parry|dodge|block/i;
  const HEAL = /you feel (?:better|much better|healthier)|heals you|your wounds/i;
  const CAST_START = /^You (?:begin casting|start to cast|utter the words)/i;
  const NOT_HERE = /they aren'?t here|you do not see that here|kill who/i;
  const SLEEP_LINE = /^You go to sleep|^You wake|^You stand up|^You sit down|^You rest/i;
  const GOLD_LINE = /you (?:get|receive|find) (\d+) (?:gold )?coins?/i;

  MH.parseLine = function parseLine(line) {
    const bus = MH.bus;
    let m;

    if (PLAYER_DEATH.test(line)) { MH.setCombat(false); bus.emit('player.death', { line }); return; }
    if ((m = line.match(MOB_DEATH))) {
      bus.emit('mob.death', { name: (m[1] || '').trim(), line });
      MH.setCombat(false);
      MH.refreshState();
      return;
    }
    if (LEVEL_UP.test(line)) { bus.emit('level.up', { line }); MH.refreshState(); return; }
    if (MOVE_BLOCKED.test(line)) { bus.emit('move.blocked', { line }); return; }
    if ((m = line.match(HIT_TARGET))) { MH.setCombat(true); bus.emit('combat.hit', { target: m[1].trim(), line }); return; }
    if ((m = line.match(MISS_TARGET))) { MH.setCombat(true); bus.emit('combat.miss', { target: m[1].trim(), line }); return; }
    if (MISSED_ME.test(line)) { MH.setCombat(true); bus.emit('combat.dodged', { line }); return; }
    if (TAKEN.test(line)) { MH.setCombat(true); bus.emit('combat.taken', { line }); return; }
    if (NOT_HERE.test(line)) { bus.emit('combat.notarget', { line }); return; }
    if (FLEE.test(line)) { MH.setCombat(false); bus.emit('combat.flee', { line }); return; }
    if (CAST_START.test(line)) { bus.emit('combat.cast', { line }); return; }
    if (HEAL.test(line)) { bus.emit('player.heal', { line }); return; }
    if ((m = line.match(GOLD_LINE))) { bus.emit('player.gold', { amount: Number(m[1]), line }); return; }
    if ((m = line.match(DOOR_OPENED))) { bus.emit('door.opened', { name: m[1], line }); MH.refreshState(); return; }
    if (SLEEP_LINE.test(line)) { bus.emit('player.posture', { line }); return; }
    if (CHAT.test(line)) { bus.emit('chat', { line }); return; }
    if (COMBAT_LINE.test(line)) { bus.emit('combat.misc', { line }); return; }
  };

  // wire the bus
  MH.bus.on('mud.line', MH.parseLine);
})();
