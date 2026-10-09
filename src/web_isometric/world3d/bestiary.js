// Which 3D body a MUD creature gets, from its name. First match wins. The cute monsters are
// mostly one big head, so they stay around half the hero's height (the KayKit hero is ~2.4 m). Models are the
// Quaternius creatures in art3d/mobs (built 1 m tall, scaled here to `h` metres), or a
// procedural body from proc.js for staples no free pack covers (rats, spiders, snakes,
// rabbits, slimes). `fly` lifts flyers off the ground; `tint` recolours untextured models.
// Undead and people are not here: they use the KayKit skeletons and adventurers.
export const BESTIARY = [
  [/\b(rat|rats|mouse|mice|rodent|vermin|giant rat)\b/, { proc: 'rat', h: 0.42 }],
  [/\b(squirrel|chipmunk|weasel|ferret|stoat|badger|otter|mole|hedgehog|porcupine|raccoon|skunk|beaver|marmot|vole|shrew)\b/, { proc: 'rat', h: 0.4, tint: 0x9a6a44 }],
  [/\b(spider|spiders|arachnid|tarantula|broodmother|spiderling)\b/, { proc: 'spider', h: 0.75 }],
  [/\b(snake|snakes|serpent|viper|asp|cobra|adder|python|anaconda|naga|rattlesnake|lizard|salamander|newt|gecko)\b/, { proc: 'snake', h: 0.45 }],
  [/\b(rabbit|rabbits|bunny|hare|jackrabbit)\b/, { proc: 'rabbit', h: 0.5 }],
  [/\b(slime|ooze|jelly|blob|pudding|gelatinous|frog|toad)\b/, { proc: 'slime', h: 0.75 }],
  [/\b(bat|bats|vampire bat)\b/, { mob: 'bat', h: 0.75, fly: 1.3 }],
  [/\b(wolf|wolves|warg|worg|direwolf)\b/, { mob: 'wolf', h: 1.0, tint: 0x8d93a0 }],
  [/\b(fox|foxes|vixen)\b/, { mob: 'fox', h: 0.7, tint: 0xd6732c }],
  [/\b(jackal|coyote|hyena)\b/, { mob: 'wolf', h: 0.85, tint: 0xbf9e6c }],
  [/\b(pug)\b/, { mob: 'pug', h: 0.55 }],
  [/\b(dog|dogs|hound|hounds|puppy|mastiff|cur|mongrel|wolfhound)\b/, { mob: 'dog', h: 0.85, tint: 0x9c6c44 }],
  [/\b(cat|cats|kitten|wildcat|alley cat)\b/, { mob: 'cat', h: 0.55, tint: 0xc78e52 }],
  [/\b(lynx|bobcat|panther|cougar|puma|lion|lioness|tiger|leopard|jaguar|sabretooth)\b/, { mob: 'cat', h: 1.15, tint: 0xd9a050 }],
  [/\bpanda\b/, { mob: 'panda', h: 1.1 }],
  [/\b(bear|bears|grizzly|ursine|bearcub|cub)\b/, { mob: 'panda', h: 1.25, tint: 0x8a5a34 }],
  [/\b(deer|doe|fawn|stag|elk|moose|reindeer|hart|antelope|gazelle)\b/, { mob: 'deer', h: 1.15 }],
  [/\b(cow|cows|bull|ox|oxen|cattle|calf|bison|buffalo|yak)\b/, { mob: 'cow', h: 1.45 }],
  [/\bzebra\b/, { mob: 'zebra', h: 1.6 }],
  [/\b(horse|horses|pony|mare|stallion|steed|colt|mule|donkey|nag|warhorse)\b/, { mob: 'horse', h: 1.75 }],
  [/\b(llama|alpaca|camel)\b/, { mob: 'llama', h: 1.6 }],
  [/\b(boar|warthog|razorback)\b/, { mob: 'farm_pig', h: 1.0, tint: 0x9a7466 }],
  [/\b(pig|pigs|hog|swine|sow|piglet)\b/, { mob: 'farm_pig', h: 0.95 }],
  [/\b(sheep|lamb|ram|ewe|goat|goats)\b/, { mob: 'sheep', h: 1.05 }],
  [/\b(chicken|chickens|hen|rooster|cockerel|fowl)\b/, { mob: 'chicken', h: 0.5 }],
  [/\b(chick|chicks|duckling)\b/, { mob: 'chick', h: 0.35 }],
  [/\b(eagle|hawk|falcon|vulture|condor|griffon|gryphon|roc)\b/, { mob: 'eagle', h: 0.75, fly: 1.6 }],
  [/\b(bird|birds|crow|crows|raven|ravens|sparrow|robin|songbird|pigeon|dove|owl|magpie|jay|finch|gull|seagull|parrot|bluebird|blackbird)\b/, { mob: 'bird', h: 0.45, fly: 1.3 }],
  [/\b(penguin|puffin)\b/, { mob: 'penguin', h: 0.7 }],
  [/\bpiranha\b/, { mob: 'piranha', h: 0.55 }],
  [/\b(shark|barracuda)\b/, { mob: 'piranha', h: 1.2, tint: 0x8a96a8 }],
  [/\b(whale|leviathan|orca)\b/, { mob: 'whale', h: 2.4 }],
  [/\b(fish|trout|salmon|carp|eel|perch|bass|pike|catfish|minnow)\b/, { mob: 'fish', h: 0.45, tint: 0x7fa8c8 }],
  [/\b(crab|crabs|lobster|crawfish|crayfish|scorpion)\b/, { mob: 'crab', h: 0.7 }],
  [/\b(bee|bees|wasp|wasps|hornet|insect|beetle|fly|flies|mosquito|dragonfly|moth|locust|firefly)\b/, { mob: 'bee', h: 0.6, fly: 1.2 }],
  [/\b(dragon|dragons|drake|wyrm|wyvern|dragonling|whelp|hatchling)\b/, { mob: 'yellowdragon', h: 1.8, fly: 0.7 }],
  [/\b(imp|imps|gremlin|quasit|homunculus|goblin)\b/, { mob: 'greendemon', h: 0.8 }],
  [/\b(demon|demons|devil|fiend|succubus|balor|daemon|hellspawn)\b/, { mob: 'demon', h: 1.3 }],
  [/\b(ghost|ghosts|spirit|spectre|specter|phantom|banshee|poltergeist|apparition|wisp|haunt|spook)\b/, { mob: 'ghost', h: 1.05, fly: 0.35 }],
  [/\b(flameskull|floating skull|skull)\b/, { mob: 'skull', h: 0.7, fly: 0.9 }],
  [/\b(cyclops|ogre|ogres|giant|giants|troll|trolls|ettin|ogrillon)\b/, { mob: 'cyclops', h: 1.7 }],
  [/\b(yeti|sasquatch|abominable|bigfoot|wendigo)\b/, { mob: 'yeti', h: 1.6 }],
  [/\b(treant|ent|dryad|sapling|shambling|walking tree|tree spirit)\b/, { mob: 'tree', h: 1.7 }],
  [/\b(mushroom|myconid|fungus|fungi|shroom|toadstool|sporeling)\b/, { mob: 'mushroom', h: 0.75 }],
  [/\bcactus\b/, { mob: 'cactus', h: 1.0 }],
  [/\b(beholder|eye tyrant|floating eye|gazer|alien)\b/, { mob: 'alien', h: 0.9, fly: 0.5 }],
  [/\b(cthulhu|kraken|octopus|squid|tentacle|horror|aberration|mind ?flayer|illithid)\b/, { mob: 'cthulhu', h: 1.2, fly: 0.3 }],
];

export function beastLook(name) {
  const n = String(name || '').toLowerCase();
  for (const [re, look] of BESTIARY) if (re.test(n)) return look;
  return null;
}
