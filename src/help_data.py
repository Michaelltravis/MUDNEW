"""
Help system data for RealmsMUD.
Contains detailed information about commands, skills, spells, and game mechanics.
"""

HELP_TOPICS = {'account': {'category': 'command',
             'description': 'View and manage your account. Usage: account [create|chars|info]',
             'syntax': 'account [create|chars|info]',
             'title': 'Account'},
 'achievements': {'category': 'command',
                  'description': 'List earned achievements and progress. Usage: achievements [all|progress]',
                  'syntax': 'achievements [all|progress]',
                  'title': 'Achievements'},
 'adrenaline_rush': {'category': 'command',
                     'description': 'Burst of speed.',
                     'syntax': 'adrenaline_rush',
                     'title': 'Adrenaline Rush'},
 'advance': {'category': 'command',
             'description': "Set a player's level (immortal only).\n\nUsage: advance <player> <level>",
             'syntax': 'advance <player> <level>',
             'title': 'Advance'},
 'aegis': {'category': 'spell',
           'classes': ['cleric'],
           'description': "Aegis\nTARGET: defensive\n\nCASTING:\n- Use `cast 'aegis'`.\n- Mana cost applies per cast.",
           'level': 1,
           'mana': 65,
           'syntax': "cast 'aegis'",
           'title': 'Aegis'},
 'ai': {'category': 'command',
        'description': 'Toggle AI chat on/off. Usage: ai on|off',
        'syntax': 'ai on|off',
        'title': 'Ai'},
 'aimed_shot': {'category': 'command',
                'description': 'Powerful ranged shot.',
                'syntax': 'aimed_shot',
                'title': 'Aimed Shot'},
 'aistatus': {'category': 'command',
              'description': 'Check AI service status (admin command).',
              'syntax': 'aistatus',
              'title': 'Aistatus'},
 'alias': {'category': 'command',
           'description': 'Create, view, or remove personal command aliases.\n'
                          '\n'
                          'Usage:\n'
                          '    alias              - List all your aliases\n'
                          '    alias <word>       - Show what <word> is aliased to\n'
                          '    alias <word> <cmd> - Create alias <word> for <cmd>\n'
                          '    unalias <word>     - Remove an alias',
           'syntax': 'alias              - List all your aliases',
           'title': 'Alias'},
 'ambush': {'category': 'skill',
            'classes': ['ranger'],
            'description': 'Launch a devastating attack from hiding.\n'
                           '\n'
                           'TRAINING:\n'
                           '- Use PRACTICE at your class trainer.\n'
                           '- Max 85% skill cap.',
            'syntax': 'ambush',
            'title': 'Ambush'},
 'animate': {'category': 'command',
             'description': 'Animate a corpse as undead. Usage: animate <corpse>',
             'syntax': 'animate <corpse>',
             'title': 'Animate'},
 'animate_dead': {'category': 'spell',
                  'classes': ['necromancer'],
                  'description': '\n'
                                 'Raise a corpse as undead.\n'
                                 '\n'
                                 'MECHANICS:\n'
                                 '- Summons a temporary undead servant\n'
                                 '- Duration scales with level\n',
                  'level': 1,
                  'mana': 50,
                  'syntax': "cast 'animate dead'",
                  'title': 'Animate Dead'},
 'answer': {'category': 'command',
            'description': 'Answer a riddle puzzle in the room.',
            'syntax': 'answer',
            'title': 'Answer'},
 'apologize': {'category': 'command', 'description': 'Apologize.', 'syntax': 'apologize', 'title': 'Apologize'},
 'armor': {'category': 'spell',
           'classes': ['bard', 'cleric', 'mage', 'necromancer'],
           'description': "Armor\nTARGET: defensive\n\nCASTING:\n- Use `cast 'armor'`.\n- Mana cost applies per cast.",
           'level': 1,
           'mana': 15,
           'syntax': "cast 'armor'",
           'title': 'Armor'},
 'ascii': {'category': 'command',
           'description': 'Toggle ASCII-only UI (no box-drawing characters). Usage: ascii [on|off]',
           'syntax': 'ascii [on|off]',
           'title': 'Ascii'},
 'ask': {'category': 'command',
         'description': 'Ask an NPC a question using LLM-powered conversation.',
         'syntax': 'ask',
         'title': 'Ask'},
 'assassin': {'category': 'class',
              'description': 'The Assassin class.\n'
                             '\n'
                             'SKILL TREE / PROGRESSION:\n'
                             '- Skills/spells unlock in the order listed for your class.\n'
                             '- Unlock tiers at levels: 2, 3, 5, 7, 10, 15, 20, 25, 30.',
              'title': 'Assassin'},
 'assassinate': {'category': 'skill',
                 'classes': ['assassin'],
                 'description': '\n'
                                'A high‑risk, high‑damage stealth finisher.\n'
                                '\n'
                                'REQUIREMENTS:\n'
                                '- Must not be in combat\n'
                                '- Piercing weapon required\n'
                                '- Best while hidden/sneaking\n'
                                '\n'
                                'MECHANICS:\n'
                                '- Uses your stealth vs target awareness\n'
                                '- Higher success on lower‑level targets\n'
                                '- Fails if target is too alert\n',
                 'syntax': 'assassinate',
                 'title': 'Assassinate'},
 'assist': {'category': 'command',
            'description': 'Help someone in combat. Usage: assist <player>',
            'syntax': 'assist <player>',
            'title': 'Assist'},
 'at': {'category': 'command',
        'description': 'Execute a command at another location (immortal only).\n'
                       '\n'
                       'Usage: at <location> <command>\n'
                       '\n'
                       'Examples:\n'
                       '    at 3001 look\n'
                       '    at 3001 mload 3000',
        'syntax': 'at <location> <command>',
        'title': 'At'},
 'attack': {'category': 'command', 'description': 'Alias for kill.', 'syntax': 'attack', 'title': 'Attack'},
 'auction': {'category': 'command',
             'description': 'Auction channel for selling items. Usage: auction <message>',
             'syntax': 'auction <message>',
             'title': 'Auction'},
 'aura': {'category': 'command', 'description': 'Activate or view paladin auras.', 'syntax': 'aura', 'title': 'Aura'},
 'autoattack': {'category': 'command',
                'description': 'Toggle automatic basic attacks.\n'
                               '\n'
                               'Usage:\n'
                               '    autoattack          - Toggle autoattack on/off\n'
                               '    autoattack on       - Turn autoattack on\n'
                               '    autoattack off      - Turn autoattack off',
                'syntax': 'autoattack          - Toggle autoattack on/off',
                'title': 'Autoattack'},
 'autocombat': {'category': 'command',
                'description': 'Toggle automatic combat skills/spells.\n'
                               '\n'
                               'Usage:\n'
                               '    autocombat          - Toggle autocombat on/off\n'
                               '    autocombat on       - Turn autocombat on\n'
                               '    autocombat off      - Turn autocombat off',
                'syntax': 'autocombat          - Toggle autocombat on/off',
                'title': 'Autocombat'},
 'autoexit': {'category': 'command',
              'description': 'Toggle automatic exit display on room entry.',
              'syntax': 'autoexit',
              'title': 'Autoexit'},
 'autogold': {'category': 'command',
              'description': 'Toggle automatic pickup of ground gold.\n'
                             '\n'
                             'Usage:\n'
                             '    autogold          - Toggle autogold on/off\n'
                             '    autogold on       - Turn autogold on\n'
                             '    autogold off      - Turn autogold off',
              'syntax': 'autogold          - Toggle autogold on/off',
              'title': 'Autogold'},
 'autoloot': {'category': 'command',
              'description': 'Toggle automatic looting of items from corpses.\n'
                             '\n'
                             'Usage:\n'
                             '    autoloot          - Toggle autoloot on/off\n'
                             '    autoloot on       - Turn autoloot on\n'
                             '    autoloot off      - Turn autoloot off\n'
                             '    autoloot gold     - Toggle gold autoloot on/off\n'
                             '    autoloot gold on  - Turn gold autoloot on\n'
                             '    autoloot gold off - Turn gold autoloot off',
              'syntax': 'autoloot          - Toggle autoloot on/off',
              'title': 'Autoloot'},
 'autorecall': {'category': 'command',
                'description': 'Set automatic recall when HP drops below a threshold.\n'
                               '\n'
                               'Usage:\n'
                               '    autorecall             - Show current autorecall settings\n'
                               '    autorecall <hp>        - Set HP threshold (number or percentage)\n'
                               '    autorecall 50          - Recall when HP drops below 50\n'
                               '    autorecall 25%         - Recall when HP drops below 25%\n'
                               '    autorecall off         - Disable autorecall',
                'syntax': 'autorecall             - Show current autorecall settings',
                'title': 'Autorecall'},
 'avatar_of_war': {'category': 'command',
                   'description': 'Massive offensive burst.',
                   'syntax': 'avatar_of_war',
                   'title': 'Avatar Of War'},
 'backstab': {'category': 'skill',
              'classes': ['assassin', 'thief'],
              'description': '\n'
                             'Backstab is a stealth opener that delivers a massive strike. It uses your\n'
                             'Sneak/Hide + environment to boost success and damage.\n'
                             '\n'
                             'REQUIREMENTS:\n'
                             '- Must not be in combat\n'
                             '- Requires a piercing weapon (dagger/knife/stiletto)\n'
                             '- Best from hidden/sneaking\n'
                             '\n'
                             'MECHANICS:\n'
                             '- Wind‑up 1–4s with spinner (can be interrupted)\n'
                             '- Success roll scales with DEX + stealth + level gap\n'
                             '- Damage multiplier scales with hidden/sneak/darkness\n'
                             '- Rare execution proc vs non‑boss targets\n'
                             '- 6s cooldown\n'
                             '\n'
                             'TIPS:\n'
                             '- Cover/snuff light to improve stealth\n'
                             '- Use hide + sneak before backstab\n',
              'syntax': 'backstab',
              'title': 'Backstab'},
 'backup': {'category': 'command',
            'description': 'Create a backup of game data (immortal only).\n'
                           '\n'
                           'Usage: backup [players|world|full]\n'
                           '       backup list\n'
                           '       backup restore <filename>',
            'syntax': 'backup [players|world|full]',
            'title': 'Backup'},
 'balance': {'category': 'command', 'description': 'Check your bank balance.', 'syntax': 'balance', 'title': 'Balance'},
 'bard': {'category': 'class',
          'description': 'The Bard class.\n'
                         '\n'
                         'SKILL TREE / PROGRESSION:\n'
                         '- Skills/spells unlock in the order listed for your class.\n'
                         '- Unlock tiers at levels: 2, 3, 5, 7, 10, 15, 20, 25, 30.',
          'title': 'Bard'},
 'barkskin': {'category': 'spell',
              'classes': ['cleric', 'ranger'],
              'description': 'Barkskin\n'
                             'TARGET: defensive\n'
                             '\n'
                             'CASTING:\n'
                             "- Use `cast 'barkskin'`.\n"
                             '- Mana cost applies per cast.',
              'level': 1,
              'mana': 40,
              'syntax': "cast 'barkskin'",
              'title': 'Barkskin'},
 'bash': {'category': 'skill',
          'classes': ['paladin', 'warrior'],
          'description': '\n'
                         'Bash to knock a target down.\n'
                         '\n'
                         'REQUIREMENTS:\n'
                         '- In combat\n'
                         '\n'
                         'MECHANICS:\n'
                         '- STR/DEX vs target\n'
                         '- On success: target knocked down (sitting)\n',
          'syntax': 'bash',
          'title': 'Bash'},
 'battleshout': {'category': 'skill',
                 'classes': ['warrior'],
                 'description': "Shout to buff party's strength and constitution.\n"
                                '\n'
                                'TRAINING:\n'
                                '- Use PRACTICE at your class trainer.\n'
                                '- Max 85% skill cap.',
                 'syntax': 'battleshout',
                 'title': 'Battleshout'},
 'bestial_wrath': {'category': 'command',
                   'description': 'Enrage your pet.',
                   'syntax': 'bestial_wrath',
                   'title': 'Bestial Wrath'},
 'bind': {'category': 'command',
          'description': 'Set your recall point to the current location.',
          'syntax': 'bind',
          'title': 'Bind'},
 'black_arrow': {'category': 'command',
                 'description': 'Poisoned arrow dealing damage over time.',
                 'syntax': 'black_arrow',
                 'title': 'Black Arrow'},
 'blade_dance': {'category': 'command',
                 'description': 'Spin striking nearby enemies.',
                 'syntax': 'blade_dance',
                 'title': 'Blade Dance'},
 'bladestorm': {'category': 'command',
                'description': 'Spin and strike all enemies.',
                'syntax': 'bladestorm',
                'title': 'Bladestorm'},
 'bless': {'category': 'spell',
           'classes': ['bard', 'cleric', 'paladin'],
           'description': "Bless\nTARGET: defensive\n\nCASTING:\n- Use `cast 'bless'`.\n- Mana cost applies per cast.",
           'level': 1,
           'mana': 15,
           'syntax': "cast 'bless'",
           'title': 'Bless'},
 'blindness': {'category': 'spell',
               'classes': ['necromancer'],
               'description': 'Blindness\n'
                              'TARGET: offensive\n'
                              '\n'
                              'CASTING:\n'
                              "- Use `cast 'blindness'`.\n"
                              '- Mana cost applies per cast.',
               'level': 1,
               'mana': 25,
               'syntax': "cast 'blindness' <target>",
               'title': 'Blindness'},
 'blink': {'category': 'spell',
           'classes': ['mage'],
           'description': "Blink\nTARGET: self\n\nCASTING:\n- Use `cast 'blink'`.\n- Mana cost applies per cast.",
           'level': 1,
           'mana': 30,
           'syntax': "cast 'blink'",
           'title': 'Blink'},
 'blur': {'category': 'skill',
          'classes': ['assassin'],
          'description': 'A class skill. Use it to gain tactical advantages in combat or utility.\n'
                         '\n'
                         'TRAINING:\n'
                         '- Use PRACTICE at your class trainer.\n'
                         '- Max 85% skill cap.',
          'syntax': 'blur',
          'title': 'Blur'},
 'blush': {'category': 'command', 'description': 'Blush.', 'syntax': 'blush', 'title': 'Blush'},
 'bow': {'category': 'command', 'description': 'Bow.', 'syntax': 'bow', 'title': 'Bow'},
 'brief': {'category': 'command',
           'description': 'Toggle brief room descriptions.\n'
                          '\n'
                          'Usage:\n'
                          '    brief          - Toggle brief mode on/off\n'
                          '    brief on       - Turn brief mode on\n'
                          '    brief off      - Turn brief mode off',
           'syntax': 'brief          - Toggle brief mode on/off',
           'title': 'Brief'},
 'bug': {'category': 'command',
         'description': 'Report a bug. Usage: bug <description>',
         'syntax': 'bug <description>',
         'title': 'Bug'},
 'burning_hands': {'category': 'spell',
                   'classes': ['mage'],
                   'description': 'Burning Hands\n'
                                  'TARGET: offensive\n'
                                  'DAMAGE: 1d6+2 + 2/level\n'
                                  '\n'
                                  'CASTING:\n'
                                  "- Use `cast 'burning hands'`.\n"
                                  '- Mana cost applies per cast.',
                   'level': 1,
                   'mana': 15,
                   'syntax': "cast 'burning hands' <target>",
                   'title': 'Burning Hands'},
 'buy': {'category': 'command',
         'description': 'Buy an item from a shop. Usage: buy <item>',
         'syntax': 'buy <item>',
         'title': 'Buy'},
 'cackle': {'category': 'command', 'description': 'Cackle.', 'syntax': 'cackle', 'title': 'Cackle'},
 'call_lightning': {'category': 'spell',
                    'classes': ['ranger'],
                    'description': 'Call Lightning\n'
                                   'TARGET: offensive\n'
                                   'DAMAGE: 4d6+5 + 2/level\n'
                                   '\n'
                                   'CASTING:\n'
                                   "- Use `cast 'call lightning'`.\n"
                                   '- Mana cost applies per cast.',
                    'level': 1,
                    'mana': 45,
                    'syntax': "cast 'call lightning' <target>",
                    'title': 'Call Lightning'},
 'camouflage': {'category': 'skill',
                'classes': ['ranger'],
                'description': '\n'
                               'Blend into terrain to reduce detection.\n'
                               '\n'
                               'MECHANICS:\n'
                               '- Bonus in forests/swamps\n'
                               '- Penalized by active light\n',
                'syntax': 'camouflage',
                'title': 'Camouflage'},
 'cast': {'category': 'command', 'description': 'Cast a spell.', 'syntax': 'cast', 'title': 'Cast'},
 'chain_lightning': {'category': 'spell',
                     'classes': ['mage'],
                     'description': 'Chain Lightning\n'
                                    'TARGET: offensive\n'
                                    'DAMAGE: 6d6+8 + 3/level\n'
                                    '\n'
                                    'CASTING:\n'
                                    "- Use `cast 'chain lightning'`.\n"
                                    '- Mana cost applies per cast.',
                     'level': 1,
                     'mana': 70,
                     'syntax': "cast 'chain lightning' <target>",
                     'title': 'Chain Lightning'},
 'changelog': {'category': 'command',
               'description': 'Alias for updates command.',
               'syntax': 'changelog',
               'title': 'Changelog'},
 'charm_person': {'category': 'spell',
                  'classes': ['bard'],
                  'description': 'Charm Person\n'
                                 'TARGET: offensive\n'
                                 '\n'
                                 'CASTING:\n'
                                 "- Use `cast 'charm person'`.\n"
                                 '- Mana cost applies per cast.',
                  'level': 1,
                  'mana': 30,
                  'syntax': "cast 'charm person' <target>",
                  'title': 'Charm Person'},
 'chat': {'category': 'command',
          'description': 'Have a dynamic AI conversation with an NPC. Usage: chat <npc> <message>',
          'syntax': 'chat <npc> <message>',
          'title': 'Chat'},
 'chathistory': {'category': 'command',
                 'description': 'Show recent AI chat history with an NPC. Usage: chathistory <npc>',
                 'syntax': 'chathistory <npc>',
                 'title': 'Chathistory'},
 'cheer': {'category': 'command', 'description': 'Cheer.', 'syntax': 'cheer', 'title': 'Cheer'},
 'chill_touch': {'category': 'spell',
                 'classes': ['mage', 'necromancer'],
                 'description': 'Chill Touch\n'
                                'TARGET: offensive\n'
                                'DAMAGE: 1d8 + 2/level\n'
                                '\n'
                                'CASTING:\n'
                                "- Use `cast 'chill touch'`.\n"
                                '- Mana cost applies per cast.',
                 'level': 1,
                 'mana': 15,
                 'syntax': "cast 'chill touch' <target>",
                 'title': 'Chill Touch'},
 'circle': {'category': 'skill',
            'classes': ['thief'],
            'description': 'Strike a distracted target for a bonus attack.',
            'syntax': 'circle',
            'title': 'Circle'},
 'clear': {'category': 'command',
           'description': 'Clear the screen.\n\nUsage: clear',
           'syntax': 'clear',
           'title': 'Clear'},
 'cleave': {'category': 'skill',
            'classes': ['warrior'],
            'description': 'Hit multiple nearby enemies with a wide swing.',
            'syntax': 'cleave',
            'title': 'Cleave'},
 'cleric': {'category': 'class',
            'description': 'The Cleric class.\n'
                           '\n'
                           'SKILL TREE / PROGRESSION:\n'
                           '- Skills/spells unlock in the order listed for your class.\n'
                           '- Unlock tiers at levels: 2, 3, 5, 7, 10, 15, 20, 25, 30.',
            'title': 'Cleric'},
 'cloak_of_shadows': {'category': 'command',
                      'description': 'Remove harmful magic effects.',
                      'syntax': 'cloak_of_shadows',
                      'title': 'Cloak Of Shadows'},
 'close': {'category': 'command',
           'description': 'Close a door or container. Usage: close <door/container>',
           'syntax': 'close <door/container>',
           'title': 'Close'},
 'cold_blood': {'category': 'command',
                'description': 'Guarantee your next attack crits.',
                'syntax': 'cold_blood',
                'title': 'Cold Blood'},
 'collections': {'category': 'command',
                 'description': 'View collection progress.',
                 'syntax': 'collections',
                 'title': 'Collections'},
 'color': {'category': 'command',
           'description': 'Set color level. Usage: color [off|sparse|normal|complete]',
           'syntax': 'color [off|sparse|normal|complete]',
           'title': 'Color'},
 'color_spray': {'category': 'spell',
                 'classes': ['mage'],
                 'description': 'Color Spray\n'
                                'TARGET: offensive\n'
                                'DAMAGE: 2d6 + 2/level\n'
                                '\n'
                                'CASTING:\n'
                                "- Use `cast 'color spray'`.\n"
                                '- Mana cost applies per cast.',
                 'level': 1,
                 'mana': 25,
                 'syntax': "cast 'color spray' <target>",
                 'title': 'Color Spray'},
 'combat': {'category': 'command',
            'description': 'Combat settings for auto-combat.\n'
                           '\n'
                           'Usage:\n'
                           '    combat settings\n'
                           '    combat settings heal <percent>\n'
                           '    combat settings skills on|off\n'
                           '    combat settings spells on|off\n'
                           '    combat settings skillpriority <skill1,skill2,...>\n'
                           '    combat settings spellpriority <spell1,spell2,...>\n'
                           '    combat settings reset',
            'syntax': 'combat settings',
            'title': 'Combat'},
 'combo': {'category': 'command', 'description': 'View current combo points.', 'syntax': 'combo', 'title': 'Combo'},
 'comfort': {'category': 'command', 'description': 'Comfort someone.', 'syntax': 'comfort', 'title': 'Comfort'},
 'commands': {'category': 'command',
              'description': 'List all available commands.',
              'syntax': 'commands',
              'title': 'Commands'},
 'compact': {'category': 'command',
             'description': 'Toggle compact combat messages.\n'
                            '\n'
                            'Usage:\n'
                            '    compact          - Toggle compact mode on/off\n'
                            '    compact on       - Turn compact mode on\n'
                            '    compact off      - Turn compact mode off',
             'syntax': 'compact          - Toggle compact mode on/off',
             'title': 'Compact'},
 'companion': {'category': 'command',
               'description': "Show your companion's stats. Usage: companion",
               'syntax': 'companion',
               'title': 'Companion'},
 'companions': {'category': 'command',
                'description': 'List your current companions. Usage: companions',
                'syntax': 'companions',
                'title': 'Companions'},
 'compare': {'category': 'command',
             'description': 'Compare a shop item to your equipped item. Usage: compare <item>',
             'syntax': 'compare <item>',
             'title': 'Compare'},
 'consider': {'category': 'command',
              'description': 'Consider how tough a mob is and learn about its capabilities.',
              'syntax': 'consider',
              'title': 'Consider'},
 'countersong': {'category': 'skill',
                 'classes': ['bard'],
                 'description': '\n'
                                'Dispel magical effects using song.\n'
                                '\n'
                                'MECHANICS:\n'
                                '- Removes buffs/debuffs from targets\n',
                 'syntax': 'countersong',
                 'title': 'Countersong'},
 'cover': {'category': 'command',
           'description': 'Cover your light source. Usage: cover light',
           'syntax': 'cover light',
           'title': 'Cover'},
 'craft': {'category': 'command', 'description': 'Craft an item from a recipe.', 'syntax': 'craft', 'title': 'Craft'},
 'create_food': {'category': 'spell',
                 'classes': ['cleric'],
                 'description': 'Create Food\n'
                                'TARGET: self\n'
                                '\n'
                                'CASTING:\n'
                                "- Use `cast 'create food'`.\n"
                                '- Mana cost applies per cast.',
                 'level': 1,
                 'mana': 10,
                 'syntax': "cast 'create food'",
                 'title': 'Create Food'},
 'create_water': {'category': 'spell',
                  'classes': ['cleric'],
                  'description': 'Create Water\n'
                                 'TARGET: self\n'
                                 '\n'
                                 'CASTING:\n'
                                 "- Use `cast 'create water'`.\n"
                                 '- Mana cost applies per cast.',
                  'level': 1,
                  'mana': 10,
                  'syntax': "cast 'create water'",
                  'title': 'Create Water'},
 'cringe': {'category': 'command', 'description': 'Cringe.', 'syntax': 'cringe', 'title': 'Cringe'},
 'crippling_poison': {'category': 'command',
                      'description': 'Apply crippling poison to your weapon.',
                      'syntax': 'crippling_poison',
                      'title': 'Crippling Poison'},
 'crusader_strike': {'category': 'command',
                     'description': 'Instant weapon strike.',
                     'syntax': 'crusader_strike',
                     'title': 'Crusader Strike'},
 'cry': {'category': 'command', 'description': 'Cry.', 'syntax': 'cry', 'title': 'Cry'},
 'cure_critical': {'category': 'spell',
                   'classes': ['cleric'],
                   'description': '\nHeal grievous wounds.\n\nMECHANICS:\n- Strong single‑target heal\n',
                   'level': 1,
                   'mana': 35,
                   'syntax': "cast 'cure critical'",
                   'title': 'Cure Critical'},
 'cure_light': {'category': 'spell',
                'classes': ['bard', 'cleric', 'paladin', 'ranger'],
                'description': 'Cure Light Wounds\n'
                               'TARGET: defensive\n'
                               '\n'
                               'CASTING:\n'
                               "- Use `cast 'cure light'`.\n"
                               '- Mana cost applies per cast.',
                'level': 1,
                'mana': 10,
                'syntax': "cast 'cure light'",
                'title': 'Cure Light'},
 'cure_serious': {'category': 'spell',
                  'classes': ['cleric', 'paladin'],
                  'description': 'Cure Serious Wounds\n'
                                 'TARGET: defensive\n'
                                 '\n'
                                 'CASTING:\n'
                                 "- Use `cast 'cure serious'`.\n"
                                 '- Mana cost applies per cast.',
                  'level': 1,
                  'mana': 20,
                  'syntax': "cast 'cure serious'",
                  'title': 'Cure Serious'},
 'daily': {'category': 'command',
           'description': 'View your daily login bonus status.\n'
                          '\n'
                          'Usage: daily\n'
                          '\n'
                          'Log in each day to build your streak and earn better rewards!',
           'syntax': 'daily',
           'title': 'Daily'},
 'dance': {'category': 'command', 'description': 'Dance.', 'syntax': 'dance', 'title': 'Dance'},
 'dc': {'category': 'command',
        'description': 'Disconnect a player (immortal only).\n\nUsage: dc <player>',
        'syntax': 'dc <player>',
        'title': 'Dc'},
 'deadly_poison': {'category': 'command',
                   'description': 'Apply deadly poison to your weapon.',
                   'syntax': 'deadly_poison',
                   'title': 'Deadly Poison'},
 'death_from_above': {'category': 'command',
                      'description': 'Leap attack for massive damage.',
                      'syntax': 'death_from_above',
                      'title': 'Death From Above'},
 'death_grip': {'category': 'spell',
                'classes': ['necromancer'],
                'description': '\nCrush a target with necrotic force.\n\nMECHANICS:\n- Strong single‑target damage\n',
                'level': 1,
                'mana': 45,
                'syntax': "cast 'death grip' <target>",
                'title': 'Death Grip'},
 'deposit': {'category': 'command',
             'description': 'Deposit gold in the bank. Usage: deposit <amount>',
             'syntax': 'deposit <amount>',
             'title': 'Deposit'},
 'detect_evil': {'category': 'spell',
                 'classes': ['paladin'],
                 'description': 'Detect Evil\n'
                                'TARGET: self\n'
                                '\n'
                                'CASTING:\n'
                                "- Use `cast 'detect evil'`.\n"
                                '- Mana cost applies per cast.',
                 'level': 1,
                 'mana': 10,
                 'syntax': "cast 'detect evil'",
                 'title': 'Detect Evil'},
 'detect_magic': {'category': 'spell',
                  'classes': ['bard', 'mage', 'ranger'],
                  'description': 'Detect Magic\n'
                                 'TARGET: self\n'
                                 '\n'
                                 'CASTING:\n'
                                 "- Use `cast 'detect magic'`.\n"
                                 '- Mana cost applies per cast.',
                  'level': 1,
                  'mana': 10,
                  'syntax': "cast 'detect magic'",
                  'title': 'Detect Magic'},
 'detect_traps': {'category': 'skill',
                  'classes': ['thief'],
                  'description': '\n'
                                 'Scan for hidden traps and dangers in the room.\n'
                                 '\n'
                                 'MECHANICS:\n'
                                 '- Skill roll vs trap difficulty\n'
                                 '- Higher skill improves detection\n',
                  'syntax': 'detect_traps',
                  'title': 'Detect Traps'},
 'diagnose': {'category': 'command',
              'description': 'Check detailed health status. Usage: diagnose [target]',
              'syntax': 'diagnose [target]',
              'title': 'Diagnose'},
 'disarm': {'category': 'skill',
            'classes': ['warrior'],
            'description': '\n'
                           'Disarm a target’s weapon.\n'
                           '\n'
                           'MECHANICS:\n'
                           '- DEX/STR vs target DEX\n'
                           '- Requires weapon in target’s hands\n',
            'syntax': 'disarm',
            'title': 'Disarm'},
 'dismiss': {'category': 'command',
             'description': 'Dismiss a pet or companion. Usage: dismiss <pet name>',
             'syntax': 'dismiss <pet name>',
             'title': 'Dismiss'},
 'dismount': {'category': 'command',
              'description': 'Dismount your current mount.',
              'syntax': 'dismount',
              'title': 'Dismount'},
 'dispel_evil': {'category': 'spell',
                 'classes': ['cleric'],
                 'description': 'Dispel Evil\n'
                                'TARGET: offensive\n'
                                'DAMAGE: 4d8 + 3/level\n'
                                '\n'
                                'CASTING:\n'
                                "- Use `cast 'dispel evil'`.\n"
                                '- Mana cost applies per cast.',
                 'level': 1,
                 'mana': 40,
                 'syntax': "cast 'dispel evil' <target>",
                 'title': 'Dispel Evil'},
 'displacement': {'category': 'spell',
                  'classes': ['mage'],
                  'description': 'Displacement\n'
                                 'TARGET: self\n'
                                 '\n'
                                 'CASTING:\n'
                                 "- Use `cast 'displacement'`.\n"
                                 '- Mana cost applies per cast.',
                  'level': 1,
                  'mana': 35,
                  'syntax': "cast 'displacement'",
                  'title': 'Displacement'},
 'display': {'category': 'command',
             'description': 'Set display options. Alias for prompt.',
             'syntax': 'display',
             'title': 'Display'},
 'divine_protection': {'category': 'spell',
                       'classes': ['cleric'],
                       'description': 'Divine Protection\n'
                                      'TARGET: self\n'
                                      '\n'
                                      'CASTING:\n'
                                      "- Use `cast 'divine protection'`.\n"
                                      '- Mana cost applies per cast.',
                       'level': 1,
                       'mana': 100,
                       'syntax': "cast 'divine protection'",
                       'title': 'Divine Protection'},
 'divine_shield': {'category': 'spell',
                   'classes': ['cleric', 'paladin'],
                   'description': '\n'
                                  'Creates a divine barrier that absorbs damage.\n'
                                  '\n'
                                  'MECHANICS:\n'
                                  '- Absorbs a fixed amount of damage\n'
                                  '- Scales with level\n',
                   'level': 1,
                   'mana': 75,
                   'syntax': "cast 'divine shield'",
                   'title': 'Divine Shield'},
 'divine_storm': {'category': 'command',
                  'description': 'Holy whirlwind attack.',
                  'syntax': 'divine_storm',
                  'title': 'Divine Storm'},
 'divinefavor': {'category': 'command',
                 'description': 'View current divine favor.',
                 'syntax': 'divinefavor',
                 'title': 'Divinefavor'},
 'dodge': {'category': 'skill',
           'classes': ['assassin', 'ranger', 'thief'],
           'description': 'Passive chance to avoid hits entirely. Higher skill = higher chance.',
           'syntax': 'dodge',
           'title': 'Dodge'},
 'donate': {'category': 'command',
            'description': 'Donate an item to help newbies. Usage: donate <item>',
            'syntax': 'donate <item>',
            'title': 'Donate'},
 'down': {'category': 'command',
          'description': 'No additional details available yet.',
          'syntax': 'down',
          'title': 'Down'},
 'drink': {'category': 'command',
           'description': 'Drink from a container or fountain.',
           'syntax': 'drink',
           'title': 'Drink'},
 'drink_alt': {'category': 'command',
               'description': 'Drink from a fountain or container. Usage: drink [from] <source>',
               'syntax': 'drink [from] <source>',
               'title': 'Drink Alt'},
 'drop': {'category': 'command', 'description': 'Drop an item or gold.', 'syntax': 'drop', 'title': 'Drop'},
 'dual_wield': {'category': 'skill',
                'classes': ['assassin', 'ranger'],
                'description': '\n'
                               'Use an off‑hand weapon.\n'
                               '\n'
                               'REQUIREMENTS:\n'
                               '- Must know dual_wield\n'
                               '- Off‑hand must be a dagger/knife/short sword\n'
                               '\n'
                               'MECHANICS:\n'
                               '- Off‑hand attacks have reduced hit/damage\n'
                               '- Scales with dual_wield skill\n',
                'syntax': 'dual_wield',
                'title': 'Dual Wield'},
 'dungeon': {'category': 'command',
             'description': 'Procedural dungeon commands.\n'
                            '\n'
                            'Usage:\n'
                            '    dungeon list\n'
                            '    dungeon enter <type> [difficulty] [permadeath]\n'
                            '    dungeon enter daily [difficulty] [permadeath]\n'
                            '    dungeon leave',
             'syntax': 'dungeon list',
             'title': 'Dungeon'},
 'earthquake': {'category': 'spell',
                'classes': ['cleric'],
                'description': 'Earthquake\n'
                               'TARGET: room\n'
                               'DAMAGE: 5d8 + 2/level\n'
                               '\n'
                               'CASTING:\n'
                               "- Use `cast 'earthquake'`.\n"
                               '- Mana cost applies per cast.',
                'level': 1,
                'mana': 90,
                'syntax': "cast 'earthquake'",
                'title': 'Earthquake'},
 'east': {'category': 'command',
          'description': 'No additional details available yet.',
          'syntax': 'east',
          'title': 'East'},
 'eat': {'category': 'command', 'description': 'Eat food.', 'syntax': 'eat', 'title': 'Eat'},
 'echo': {'category': 'command',
          'description': 'Send a message to the current room (immortal only).\n\nUsage: echo <message>',
          'syntax': 'echo <message>',
          'title': 'Echo'},
 'emote': {'category': 'command', 'description': 'Emote an action.', 'syntax': 'emote', 'title': 'Emote'},
 'enchant_weapon': {'category': 'spell',
                    'classes': ['mage'],
                    'description': 'Enchant Weapon\n'
                                   'TARGET: object\n'
                                   '\n'
                                   'CASTING:\n'
                                   "- Use `cast 'enchant weapon'`.\n"
                                   '- Mana cost applies per cast.',
                    'level': 1,
                    'mana': 100,
                    'syntax': "cast 'enchant weapon'",
                    'title': 'Enchant Weapon'},
 'encore': {'category': 'command',
            'description': "Boost your current song's effects temporarily.",
            'syntax': 'encore',
            'title': 'Encore'},
 'energy_drain': {'category': 'spell',
                  'classes': ['necromancer'],
                  'description': 'Energy Drain\n'
                                 'TARGET: offensive\n'
                                 'DAMAGE: 3d8 + 2/level\n'
                                 '\n'
                                 'CASTING:\n'
                                 "- Use `cast 'energy drain'`.\n"
                                 '- Mana cost applies per cast.',
                  'level': 1,
                  'mana': 60,
                  'syntax': "cast 'energy drain' <target>",
                  'title': 'Energy Drain'},
 'enervation': {'category': 'spell',
                'classes': ['necromancer'],
                'description': '\nDrain life force, weakening a target.\n\nMECHANICS:\n- Damage + debuff\n',
                'level': 1,
                'mana': 35,
                'syntax': "cast 'enervation' <target>",
                'title': 'Enervation'},
 'entangle': {'category': 'spell',
              'classes': ['ranger'],
              'description': 'Entangle\n'
                             'TARGET: offensive\n'
                             '\n'
                             'CASTING:\n'
                             "- Use `cast 'entangle'`.\n"
                             '- Mana cost applies per cast.',
              'level': 1,
              'mana': 25,
              'syntax': "cast 'entangle' <target>",
              'title': 'Entangle'},
 'enter': {'category': 'command',
           'description': 'Enter a building or portal. Usage: enter [portal/building name]',
           'syntax': 'enter [portal/building name]',
           'title': 'Enter'},
 'envenom': {'category': 'skill',
             'classes': ['assassin'],
             'description': '\n'
                            'Coat your blade with poison for extra damage.\n'
                            '\n'
                            'MECHANICS:\n'
                            '- Adds poison damage on hits for a short duration\n'
                            '- Stronger with higher skill\n',
             'syntax': 'envenom',
             'title': 'Envenom'},
 'equipment': {'category': 'command',
               'description': 'Show equipped items.',
               'syntax': 'equipment',
               'title': 'Equipment'},
 'evasion': {'category': 'skill',
             'classes': ['assassin', 'thief'],
             'description': 'Passive chance to evade attacks entirely (best for rogues).',
             'syntax': 'evasion',
             'title': 'Evasion'},
 'eviscerate': {'category': 'command',
                'description': 'Powerful finisher that consumes all combo points.',
                'syntax': 'eviscerate',
                'title': 'Eviscerate'},
 'examine': {'category': 'command',
             'description': 'Examine an item in your inventory or equipment. Usage: examine <item>',
             'syntax': 'examine <item>',
             'title': 'Examine'},
 'execute': {'category': 'command',
             'description': 'Devastating finisher that deals more damage at low target HP.',
             'syntax': 'execute',
             'title': 'Execute'},
 'exits': {'category': 'command',
           'description': 'Show available exits from the current room with descriptions.',
           'syntax': 'exits',
           'title': 'Exits'},
 'explosive_trap': {'category': 'command',
                    'description': 'Set an explosive trap in the room.',
                    'syntax': 'explosive_trap',
                    'title': 'Explosive Trap'},
 'faction': {'category': 'command',
             'description': 'Show detailed reputation for a specific faction.',
             'syntax': 'faction',
             'title': 'Faction'},
 'faerie_fire': {'category': 'spell',
                 'classes': ['ranger'],
                 'description': 'Faerie Fire\n'
                                'TARGET: offensive\n'
                                '\n'
                                'CASTING:\n'
                                "- Use `cast 'faerie fire'`.\n"
                                '- Mana cost applies per cast.',
                 'level': 1,
                 'mana': 20,
                 'syntax': "cast 'faerie fire' <target>",
                 'title': 'Faerie Fire'},
 'fascinate': {'category': 'skill',
               'classes': ['bard'],
               'description': '\n'
                              'Charm and pacify a target.\n'
                              '\n'
                              'MECHANICS:\n'
                              '- Target must be out of combat\n'
                              '- Breaks if target is attacked\n',
               'syntax': 'fascinate',
               'title': 'Fascinate'},
 'fear': {'category': 'spell',
          'classes': ['bard', 'necromancer'],
          'description': "Fear\nTARGET: offensive\n\nCASTING:\n- Use `cast 'fear'`.\n- Mana cost applies per cast.",
          'level': 1,
          'mana': 30,
          'syntax': "cast 'fear' <target>",
          'title': 'Fear'},
 'feint': {'category': 'skill',
           'classes': ['assassin'],
           'description': 'Briefly lowers target defenses; improves your next hit.',
           'syntax': 'feint',
           'title': 'Feint'},
 'fill': {'category': 'command',
          'description': 'Fill a container from a fountain. Usage: fill <container> [fountain]',
          'syntax': 'fill <container> [fountain]',
          'title': 'Fill'},
 'find': {'category': 'command',
          'description': 'Find a mob or object anywhere in the world (immortal only).\n'
                         '\n'
                         'Usage:\n'
                         '    find mob <name>    - Find all mobs matching name\n'
                         '    find obj <name>    - Find all objects matching name',
          'syntax': 'find mob <name>    - Find all mobs matching name',
          'title': 'Find'},
 'finger_of_death': {'category': 'spell',
                     'classes': ['necromancer'],
                     'description': '\n'
                                    'Deadly necrotic spell.\n'
                                    '\n'
                                    'MECHANICS:\n'
                                    '- Heavy damage\n'
                                    '- Can execute targets below 25% HP\n'
                                    '- Bosses immune\n',
                     'level': 1,
                     'mana': 150,
                     'syntax': "cast 'finger of death' <target>",
                     'title': 'Finger Of Death'},
 'fire_shield': {'category': 'spell',
                 'classes': ['mage'],
                 'description': 'Fire Shield\n'
                                'TARGET: self\n'
                                '\n'
                                'CASTING:\n'
                                "- Use `cast 'fire shield'`.\n"
                                '- Mana cost applies per cast.',
                 'level': 1,
                 'mana': 50,
                 'syntax': "cast 'fire shield'",
                 'title': 'Fire Shield'},
 'fireball': {'category': 'spell',
              'classes': ['mage'],
              'description': '\n'
                             'Hurl a fireball at a target.\n'
                             '\n'
                             'MECHANICS:\n'
                             '- Damage scales with level\n'
                             '- Single‑target burst\n',
              'level': 1,
              'mana': 40,
              'syntax': "cast 'fireball' <target>",
              'title': 'Fireball'},
 'flamestrike': {'category': 'spell',
                 'classes': ['cleric'],
                 'description': 'Flamestrike\n'
                                'TARGET: offensive\n'
                                'DAMAGE: 4d8+10 + 2/level\n'
                                '\n'
                                'CASTING:\n'
                                "- Use `cast 'flamestrike'`.\n"
                                '- Mana cost applies per cast.',
                 'level': 1,
                 'mana': 60,
                 'syntax': "cast 'flamestrike' <target>",
                 'title': 'Flamestrike'},
 'flee': {'category': 'command', 'description': 'Flee from combat.', 'syntax': 'flee', 'title': 'Flee'},
 'fly': {'category': 'spell',
         'classes': ['mage'],
         'description': "Fly\nTARGET: defensive\n\nCASTING:\n- Use `cast 'fly'`.\n- Mana cost applies per cast.",
         'level': 1,
         'mana': 30,
         'syntax': "cast 'fly'",
         'title': 'Fly'},
 'follow': {'category': 'command',
            'description': 'Follow another player. Usage: follow <player> or follow self',
            'syntax': 'follow <player> or follow self',
            'title': 'Follow'},
 'force': {'category': 'command',
           'description': 'Force a player to execute a command (immortal only).\n\nUsage: force <player> <command>',
           'syntax': 'force <player> <command>',
           'title': 'Force'},
 'freeze': {'category': 'command',
            'description': "Freeze a player so they can't do anything (immortal only).\n\nUsage: freeze <player>",
            'syntax': 'freeze <player>',
            'title': 'Freeze'},
 'garrote': {'category': 'skill',
             'classes': ['assassin'],
             'description': '\n'
                            'Ambush that constricts a target, disrupting them.\n'
                            '\n'
                            'REQUIREMENTS:\n'
                            '- Must not be in combat\n'
                            '- Target in room\n'
                            '\n'
                            'MECHANICS:\n'
                            '- Uses stealth roll vs target detection\n'
                            '- On success: bonus damage + short control window\n',
             'syntax': 'garrote',
             'title': 'Garrote'},
 'gather': {'category': 'command',
            'description': 'Gather resources based on environment.',
            'syntax': 'gather',
            'title': 'Gather'},
 'gecho': {'category': 'command',
           'description': 'Send a message to all players (immortal only).\n\nUsage: gecho <message>',
           'syntax': 'gecho <message>',
           'title': 'Gecho'},
 'get': {'category': 'command',
         'description': 'Pick up an item.\n'
                        '\n'
                        'Usage:\n'
                        '    get <item>              - Get item from room\n'
                        '    get all                 - Get all items from room\n'
                        '    get <item> <container>  - Get item from container\n'
                        '    get all <container>     - Get all items from container\n'
                        '    get <item> from <container> - Alternative syntax\n'
                        '    get all from <container>    - Alternative syntax',
         'syntax': 'get <item>              - Get item from room',
         'title': 'Get'},
 'giggle': {'category': 'command', 'description': 'Giggle.', 'syntax': 'giggle', 'title': 'Giggle'},
 'give': {'category': 'command', 'description': 'Give an item to someone.', 'syntax': 'give', 'title': 'Give'},
 'glare': {'category': 'command', 'description': 'Glare at someone.', 'syntax': 'glare', 'title': 'Glare'},
 'gossip': {'category': 'command',
            'description': 'Global chat channel. Usage: gossip <message>',
            'syntax': 'gossip <message>',
            'title': 'Gossip'},
 'goto': {'category': 'command',
          'description': 'Teleport to a room or zone (testing command).\n'
                         '\n'
                         'Usage:\n'
                         '    goto <vnum>     - Go to room vnum (e.g. goto 3001)\n'
                         '    goto <zone>     - Go to zone entrance (e.g. goto 30)',
          'syntax': 'goto <vnum>     - Go to room vnum (e.g. goto 3001)',
          'title': 'Goto'},
 'grats': {'category': 'command',
           'description': 'Congratulations channel. Usage: grats <message>',
           'syntax': 'grats <message>',
           'title': 'Grats'},
 'greet': {'category': 'command', 'description': 'Greet someone.', 'syntax': 'greet', 'title': 'Greet'},
 'grin': {'category': 'command', 'description': 'Grin.', 'syntax': 'grin', 'title': 'Grin'},
 'group': {'category': 'command',
           'description': 'Manage your group. CircleMUD-style group commands.\n'
                          '\n'
                          'Usage:\n'
                          '    group           - Show group status\n'
                          '    group all       - Group all players following you\n'
                          '    group <player>  - Add a player following you to your group\n'
                          '    group leave     - Leave your current group\n'
                          '    group disband   - Disband the group (leader only)\n'
                          '    group kick <n>  - Remove player from group (leader only)',
           'syntax': 'group           - Show group status',
           'title': 'Group'},
 'group_heal': {'category': 'spell',
                'classes': ['cleric'],
                'description': 'Group Heal\n'
                               'TARGET: group\n'
                               '\n'
                               'CASTING:\n'
                               "- Use `cast 'group heal'`.\n"
                               '- Mana cost applies per cast.',
                'level': 1,
                'mana': 80,
                'syntax': "cast 'group heal'",
                'title': 'Group Heal'},
 'grumble': {'category': 'command', 'description': 'Grumble.', 'syntax': 'grumble', 'title': 'Grumble'},
 'gtell': {'category': 'command',
           'description': 'Send a message to your group. Usage: gtell <message>',
           'syntax': 'gtell <message>',
           'title': 'Gtell'},
 'harm': {'category': 'spell',
          'classes': ['cleric'],
          'description': 'Harm\n'
                         'TARGET: offensive\n'
                         'DAMAGE: 5d8\n'
                         '\n'
                         'CASTING:\n'
                         "- Use `cast 'harm'`.\n"
                         '- Mana cost applies per cast.',
          'level': 1,
          'mana': 50,
          'syntax': "cast 'harm' <target>",
          'title': 'Harm'},
 'haste': {'category': 'spell',
           'classes': ['bard'],
           'description': '\nMagically hasten allies.\n\nMECHANICS:\n- Extra attacks / move speed\n- Short duration\n',
           'level': 1,
           'mana': 50,
           'syntax': "cast 'haste'",
           'title': 'Haste'},
 'heal': {'category': 'spell',
          'classes': ['cleric'],
          'description': '\n'
                         'Restore major HP to a target.\n'
                         '\n'
                         'MECHANICS:\n'
                         '- Scaling with level and heal power\n'
                         '- Higher mana cost, strong single target\n',
          'level': 1,
          'mana': 50,
          'syntax': "cast 'heal'",
          'title': 'Heal'},
 'help': {'category': 'command',
          'description': 'Show help information for commands, skills, and spells.',
          'syntax': 'help',
          'title': 'Help'},
 'heroism': {'category': 'spell',
             'classes': ['bard'],
             'description': 'Heroism\n'
                            'TARGET: defensive\n'
                            '\n'
                            'CASTING:\n'
                            "- Use `cast 'heroism'`.\n"
                            '- Mana cost applies per cast.',
             'level': 1,
             'mana': 40,
             'syntax': "cast 'heroism'",
             'title': 'Heroism'},
 'hide': {'category': 'skill',
          'classes': ['assassin', 'ranger', 'thief'],
          'description': '\n'
                         'Blend into shadows to avoid detection.\n'
                         '\n'
                         'MECHANICS:\n'
                         '- Hide roll uses skill + environment\n'
                         '- Dark/forest/swamp boost; active light penalizes\n'
                         '- Successful hide can break tracking\n'
                         '\n'
                         'TIPS:\n'
                         '- Hide before backstab for a big damage bonus\n',
          'syntax': 'hide',
          'title': 'Hide'},
 'hint': {'category': 'command',
          'description': 'Request a hint for the current room puzzle.',
          'syntax': 'hint',
          'title': 'Hint'},
 'hire': {'category': 'command',
          'description': 'Hire a companion from a tavern or guild. Usage: hire <npc>',
          'syntax': 'hire <npc>',
          'title': 'Hire'},
 'holler': {'category': 'command',
            'description': 'Shout to everyone (costs 20 movement). Usage: holler <message>',
            'syntax': 'holler <message>',
            'title': 'Holler'},
 'holy_aura': {'category': 'spell',
               'classes': ['cleric'],
               'description': 'Holy Aura\n'
                              'TARGET: defensive\n'
                              '\n'
                              'CASTING:\n'
                              "- Use `cast 'holy aura'`.\n"
                              '- Mana cost applies per cast.',
               'level': 1,
               'mana': 80,
               'syntax': "cast 'holy aura'",
               'title': 'Holy Aura'},
 'holy_smite': {'category': 'skill',
                'classes': ['cleric'],
                'description': '\n'
                               'Spend divine favor to smite a target.\n'
                               '\n'
                               'MECHANICS:\n'
                               '- Bonus damage vs undead/evil\n'
                               '- Scales with favor\n',
                'syntax': 'holy_smite',
                'title': 'Holy Smite'},
 'holylight': {'category': 'command',
               'description': 'Toggle ability to see everything (dark rooms, invisible, etc) (immortal only).\n'
                              '\n'
                              'Usage: holylight',
               'syntax': 'holylight',
               'title': 'Holylight'},
 'holysmite': {'category': 'command',
               'description': 'Spend divine favor for a powerful holy attack.',
               'syntax': 'holysmite',
               'title': 'Holysmite'},
 'house': {'category': 'command',
           'description': 'Manage housing. Usage: house [buy|info]',
           'syntax': 'house [buy|info]',
           'title': 'House'},
 'hug': {'category': 'command', 'description': 'Hug someone.', 'syntax': 'hug', 'title': 'Hug'},
 'hunters_mark': {'category': 'command',
                  'description': 'Mark a target for increased damage from your attacks.',
                  'syntax': 'hunters_mark',
                  'title': 'Hunters Mark'},
 'ice_armor': {'category': 'spell',
               'classes': ['mage'],
               'description': 'Ice Armor\n'
                              'TARGET: defensive\n'
                              '\n'
                              'CASTING:\n'
                              "- Use `cast 'ice armor'`.\n"
                              '- Mana cost applies per cast.',
               'level': 1,
               'mana': 45,
               'syntax': "cast 'ice armor'",
               'title': 'Ice Armor'},
 'idea': {'category': 'command',
          'description': 'Suggest an idea. Usage: idea <your suggestion>',
          'syntax': 'idea <your suggestion>',
          'title': 'Idea'},
 'identify': {'category': 'spell',
              'classes': ['mage'],
              'description': 'Identify\n'
                             'TARGET: object\n'
                             '\n'
                             'CASTING:\n'
                             "- Use `cast 'identify'`.\n"
                             '- Mana cost applies per cast.',
              'level': 1,
              'mana': 20,
              'syntax': "cast 'identify'",
              'title': 'Identify'},
 'ignorepain': {'category': 'command',
                'description': 'Absorb incoming damage with pure willpower.',
                'syntax': 'ignorepain',
                'title': 'Ignorepain'},
 'imbue': {'category': 'command',
           'description': 'Imbue a corpse with soulstone power. Usage: imbue [corpse]',
           'syntax': 'imbue [corpse]',
           'title': 'Imbue'},
 'immlist': {'category': 'command',
             'description': 'List all immortals (admin accounts).\n\nUsage: immlist',
             'syntax': 'immlist',
             'title': 'Immlist'},
 'info': {'category': 'command',
          'description': 'Display game information for new players.',
          'syntax': 'info',
          'title': 'Info'},
 'interrupt': {'category': 'command',
               'description': 'Attempt to interrupt a boss cast with bash or kick.',
               'syntax': 'interrupt',
               'title': 'Interrupt'},
 'intimidate': {'category': 'skill',
                'classes': ['warrior'],
                'description': 'A class skill. Use it to gain tactical advantages in combat or utility.\n'
                               '\n'
                               'TRAINING:\n'
                               '- Use PRACTICE at your class trainer.\n'
                               '- Max 85% skill cap.',
                'syntax': 'intimidate',
                'title': 'Intimidate'},
 'inventory': {'category': 'command', 'description': 'Show inventory.', 'syntax': 'inventory', 'title': 'Inventory'},
 'invis': {'category': 'command',
           'description': 'List all invisible players/mobs in room (immortal only).\n\nUsage: invis',
           'syntax': 'invis',
           'title': 'Invis'},
 'invisibility': {'category': 'spell',
                  'classes': ['bard', 'mage'],
                  'description': '\n'
                                 'Become invisible to enemies.\n'
                                 '\n'
                                 'MECHANICS:\n'
                                 '- Breaks on attack\n'
                                 '- Improves stealth rolls\n',
                  'level': 1,
                  'mana': 35,
                  'syntax': "cast 'invisibility'",
                  'title': 'Invisibility'},
 'journal': {'category': 'command',
             'description': 'Review your discovery journal.\n'
                            '\n'
                            'Usage:\n'
                            '    journal              - Show journal overview and recent entries\n'
                            '    journal stats        - Show discovery statistics\n'
                            '    journal lore         - Show lore entries\n'
                            '    journal secrets      - Show discovered secrets\n'
                            "    journal npcs         - Show NPCs you've met\n"
                            '    journal areas        - Show discovered areas\n'
                            '    journal read <num>   - Read a specific entry\n'
                            '    journal all          - Show all entries',
             'syntax': 'journal              - Show journal overview and recent entries',
             'title': 'Journal'},
 'judgment': {'category': 'command', 'description': 'Ranged holy strike.', 'syntax': 'judgment', 'title': 'Judgment'},
 'junk': {'category': 'command',
          'description': 'Destroy an item. Usage: junk <item>',
          'syntax': 'junk <item>',
          'title': 'Junk'},
 'kick': {'category': 'skill',
          'classes': ['warrior'],
          'description': 'Kick a target for extra damage.\n\nMECHANICS:\n- Usable in combat\n- Scales with STR\n',
          'syntax': 'kick',
          'title': 'Kick'},
 'kidneyshot': {'category': 'command',
                'description': 'Stun finisher that uses 4+ combo points.',
                'syntax': 'kidneyshot',
                'title': 'Kidneyshot'},
 'kill': {'category': 'command', 'description': 'Attack a target.', 'syntax': 'kill', 'title': 'Kill'},
 'killing_spree': {'category': 'command',
                   'description': 'Rapidly strike multiple enemies.',
                   'syntax': 'killing_spree',
                   'title': 'Killing Spree'},
 'knock': {'category': 'command',
           'description': 'Knock on a door. Usage: knock <direction>',
           'syntax': 'knock <direction>',
           'title': 'Knock'},
 'label': {'category': 'command',
           'description': 'Label a target for quick targeting in combat.\n'
                          '\n'
                          'Usage:\n'
                          '    label                    - Show all current labels\n'
                          '    label <target> <name>    - Label a target (e.g., label warrior DEAD)\n'
                          '    label clear              - Clear all labels\n'
                          '    label clear <name>       - Clear specific label\n'
                          '\n'
                          'Then use the label in commands: kill DEAD, cast fireball DEAD\n'
                          'Labels are case-insensitive and session-only (not saved).',
           'syntax': 'label                    - Show all current labels',
           'title': 'Label'},
 'laugh': {'category': 'command', 'description': 'Laugh.', 'syntax': 'laugh', 'title': 'Laugh'},
 'layhands': {'category': 'command',
              'description': 'Use lay on hands to heal yourself or an ally.',
              'syntax': 'layhands',
              'title': 'Layhands'},
 'leaderboard': {'category': 'command',
                 'description': 'View the server leaderboards.\n'
                                '\n'
                                'Usage: leaderboard [category]\n'
                                'Categories: level, kills, gold, deaths, achievements, quests',
                 'syntax': 'leaderboard [category]',
                 'title': 'Leaderboard'},
 'leave': {'category': 'command',
           'description': 'Leave a building to go outside. Usage: leave',
           'syntax': 'leave',
           'title': 'Leave'},
 'levels': {'category': 'command',
            'description': 'Show experience required for each level.',
            'syntax': 'levels',
            'title': 'Levels'},
 'lightning_bolt': {'category': 'spell',
                    'classes': ['mage'],
                    'description': '\n'
                                   'Strike a target with lightning.\n'
                                   '\n'
                                   'MECHANICS:\n'
                                   '- Damage scales with level\n'
                                   '- Offensive spell\n',
                    'level': 1,
                    'mana': 35,
                    'syntax': "cast 'lightning bolt' <target>",
                    'title': 'Lightning Bolt'},
 'list': {'category': 'command',
          'description': 'List items for sale in a shop. Usage: list',
          'syntax': 'list',
          'title': 'List'},
 'load': {'category': 'command',
          'description': 'Load a mob or object (immortal only).\n'
                         '\n'
                         'Usage:\n'
                         '    load mob <vnum>       - Load a mob\n'
                         '    load obj <vnum>       - Load an object to inventory\n'
                         '    load obj <vnum> room  - Load an object to room',
          'syntax': 'load mob <vnum>       - Load a mob',
          'title': 'Load'},
 'lock': {'category': 'command',
          'description': 'Lock a door or container. Usage: lock <door/container>',
          'syntax': 'lock <door/container>',
          'title': 'Lock'},
 'look': {'category': 'command', 'description': 'Look at the room or something.', 'syntax': 'look', 'title': 'Look'},
 'loot': {'category': 'command',
          'description': 'Loot items from a corpse. Supports numbered targeting (e.g., loot 2.corpse)',
          'syntax': 'loot',
          'title': 'Loot'},
 'lore': {'category': 'skill',
          'classes': ['bard'],
          'description': 'Review discovered lore.\n'
                         '\n'
                         'TRAINING:\n'
                         '- Use PRACTICE at your class trainer.\n'
                         '- Max 85% skill cap.',
          'syntax': 'lore',
          'title': 'Lore'},
 'mage': {'category': 'class',
          'description': 'The Mage class.\n'
                         '\n'
                         'SKILL TREE / PROGRESSION:\n'
                         '- Skills/spells unlock in the order listed for your class.\n'
                         '- Unlock tiers at levels: 2, 3, 5, 7, 10, 15, 20, 25, 30.',
          'title': 'Mage'},
 'magic_missile': {'category': 'spell',
                   'classes': ['mage'],
                   'description': 'Magic Missile\n'
                                  'TARGET: offensive\n'
                                  'DAMAGE: 1d4+1 + 1/level\n'
                                  '\n'
                                  'CASTING:\n'
                                  "- Use `cast 'magic missile'`.\n"
                                  '- Mana cost applies per cast.',
                   'level': 1,
                   'mana': 10,
                   'syntax': "cast 'magic missile' <target>",
                   'title': 'Magic Missile'},
 'mana_shield': {'category': 'spell',
                 'classes': ['mage'],
                 'description': 'Mana Shield\n'
                                'TARGET: self\n'
                                '\n'
                                'CASTING:\n'
                                "- Use `cast 'mana shield'`.\n"
                                '- Mana cost applies per cast.',
                 'level': 1,
                 'mana': 50,
                 'syntax': "cast 'mana shield'",
                 'title': 'Mana Shield'},
 'map': {'category': 'command',
         'description': 'Display ASCII map.\n'
                        '\n'
                        'Usage:\n'
                        '    map        - Show local explored map\n'
                        '    map full   - Show entire explored area\n'
                        '    map zone   - Show explored rooms in current zone',
         'syntax': 'map        - Show local explored map',
         'title': 'Map'},
 'mapurl': {'category': 'command',
            'description': 'Show the web map URL for this player.',
            'syntax': 'mapurl',
            'title': 'Mapurl'},
 'mark': {'category': 'command',
          'description': 'Mark a target for death, increasing damage against them.',
          'syntax': 'mark',
          'title': 'Mark'},
 'mark_target': {'category': 'skill',
                 'classes': ['assassin'],
                 'description': '\n'
                                'Mark a target to improve accuracy and track them.\n'
                                '\n'
                                'EFFECTS:\n'
                                '- Improves hit chance vs marked target\n'
                                '- Used for coordinated burst\n',
                 'syntax': 'mark_target',
                 'title': 'Mark Target'},
 'marked_for_death': {'category': 'command',
                      'description': 'Mark a target for lethal focus.',
                      'syntax': 'marked_for_death',
                      'title': 'Marked For Death'},
 'marked_shot': {'category': 'command',
                 'description': 'Fire a powerful shot at a marked target for bonus damage.',
                 'syntax': 'marked_shot',
                 'title': 'Marked Shot'},
 'mass_charm': {'category': 'spell',
                'classes': ['bard'],
                'description': 'Mass Charm\n'
                               'TARGET: room\n'
                               '\n'
                               'CASTING:\n'
                               "- Use `cast 'mass charm'`.\n"
                               '- Mana cost applies per cast.',
                'level': 1,
                'mana': 100,
                'syntax': "cast 'mass charm'",
                'title': 'Mass Charm'},
 'medit': {'category': 'command',
           'description': 'Online mob editor (immortal only).',
           'syntax': 'medit',
           'title': 'Medit'},
 'meteor_swarm': {'category': 'spell',
                  'classes': ['mage'],
                  'description': '\n'
                                 'Call down a swarm of meteors.\n'
                                 '\n'
                                 'MECHANICS:\n'
                                 '- Heavy AoE damage\n'
                                 '- High mana cost\n',
                  'level': 1,
                  'mana': 80,
                  'syntax': "cast 'meteor swarm' <target>",
                  'title': 'Meteor Swarm'},
 'minimap': {'category': 'command',
             'description': 'Display a compact ASCII minimap centered on the player.',
             'syntax': 'minimap',
             'title': 'Minimap'},
 'minions': {'category': 'command',
             'description': 'List your summoned minions (undead, summons). Usage: minions',
             'syntax': 'minions',
             'title': 'Minions'},
 'mirror_image': {'category': 'spell',
                  'classes': ['mage'],
                  'description': 'Mirror Image\n'
                                 'TARGET: self\n'
                                 '\n'
                                 'CASTING:\n'
                                 "- Use `cast 'mirror image'`.\n"
                                 '- Mana cost applies per cast.',
                  'level': 1,
                  'mana': 40,
                  'syntax': "cast 'mirror image'",
                  'title': 'Mirror Image'},
 'mlist': {'category': 'command',
           'description': 'List all mobs in a zone (immortal only).\n'
                          '\n'
                          'Usage:\n'
                          '    mlist           - List mobs in current zone\n'
                          '    mlist <zone>    - List mobs in specified zone',
           'syntax': 'mlist           - List mobs in current zone',
           'title': 'Mlist'},
 'mload': {'category': 'command',
           'description': 'Load a mob into the current room (immortal only).\n\nUsage: mload <vnum>',
           'syntax': 'mload <vnum>',
           'title': 'Mload'},
 'mock': {'category': 'command',
          'description': 'Taunt an enemy with vicious mockery, debuffing them.',
          'syntax': 'mock',
          'title': 'Mock'},
 'mockery': {'category': 'skill',
             'classes': ['bard'],
             'description': '\n'
                            'Psychic taunt that damages and debuffs.\n'
                            '\n'
                            'MECHANICS:\n'
                            '- Deals psychic damage\n'
                            '- Reduces hitroll briefly\n',
             'syntax': 'mockery',
             'title': 'Mockery'},
 'mortal_strike': {'category': 'command',
                   'description': 'Heavy strike that wounds the target.',
                   'syntax': 'mortal_strike',
                   'title': 'Mortal Strike'},
 'motd': {'category': 'command', 'description': 'Display the Message of the Day.', 'syntax': 'motd', 'title': 'Motd'},
 'mount': {'category': 'command',
           'description': 'Mount a owned/tamed mount. Usage: mount [name]',
           'syntax': 'mount [name]',
           'title': 'Mount'},
 'mounts': {'category': 'command', 'description': 'List your owned mounts.', 'syntax': 'mounts', 'title': 'Mounts'},
 'move': {'category': 'command', 'description': 'Move in a direction.', 'syntax': 'move', 'title': 'Move'},
 'mute': {'category': 'command',
          'description': "Mute a player so they can't talk (immortal only).\n\nUsage: mute <player>",
          'syntax': 'mute <player>',
          'title': 'Mute'},
 'mutilate': {'category': 'command',
              'description': 'Dual strike that builds combo points.',
              'syntax': 'mutilate',
              'title': 'Mutilate'},
 'necromancer': {'category': 'class',
                 'description': 'Necromancers wield death magic, draining life and commanding the dead. They\n'
                                'excel at sustained pressure, debuffs, and undead minions, but are fragile\n'
                                'in direct melee.\n'
                                '\n'
                                'PLAYSTYLE:\n'
                                '- Open with debuffs (blindness, poison) and drain effects\n'
                                '- Use undead minions for frontline pressure\n'
                                '- Sustain with life drain and mana management\n'
                                '\n'
                                'RESOURCE LOOP:\n'
                                '- Mana fuels most damage; conserve with efficient drains\n'
                                '- Soul fragments extend undead duration (if available)\n'
                                '\n'
                                'PETS / MINIONS:\n'
                                '- Animate Dead creates temporary undead\n'
                                '- Undead minions persist for their duration and assist in combat\n'
                                '\n'
                                'DEFENSES:\n'
                                '- Armor/Shield spells improve survivability\n'
                                '- Keep distance; rely on control and minions\n'
                                '\n'
                                'SKILL TREE / PROGRESSION:\n'
                                '- Skills/spells unlock in the order listed for your class.\n'
                                '- Unlock tiers at levels: 2, 3, 5, 7, 10, 15, 20, 25, 30.\n'
                                '\n'
                                'SPELL ORDER:\n'
                                '- 1. Chill Touch\n'
                                '- 2. Animate Dead\n'
                                '- 3. Vampiric Touch\n'
                                '- 4. Enervation\n'
                                '- 5. Death Grip\n'
                                '- 6. Finger Of Death\n'
                                '- 7. Energy Drain\n'
                                '- 8. Poison\n'
                                '- 9. Weaken\n'
                                '- 10. Blindness\n'
                                '- 11. Fear\n'
                                '- 12. Armor\n'
                                '- 13. Shield\n'
                                '- 14. Protection From Good\n'
                                '\n'
                                'TRAINING:\n'
                                '- Use PRACTICE at your class trainer.',
                 'title': 'Necromancer'},
 'newgameplus': {'category': 'command',
                 'description': 'Start a New Game+ cycle after completing the main story.',
                 'syntax': 'newgameplus',
                 'title': 'Newgameplus'},
 'news': {'category': 'command', 'description': 'Alias for updates command.', 'syntax': 'news', 'title': 'News'},
 'nod': {'category': 'command', 'description': 'Nod.', 'syntax': 'nod', 'title': 'Nod'},
 'nohassle': {'category': 'command',
              'description': 'Toggle immunity to mob attacks (immortal only).\n\nUsage: nohassle',
              'syntax': 'nohassle',
              'title': 'Nohassle'},
 'norepeat': {'category': 'command',
              'description': 'Toggle echoing of your own communication.',
              'syntax': 'norepeat',
              'title': 'Norepeat'},
 'north': {'category': 'command',
           'description': 'No additional details available yet.',
           'syntax': 'north',
           'title': 'North'},
 'noshout': {'category': 'command',
             'description': 'Toggle blocking of shouts and hollers.',
             'syntax': 'noshout',
             'title': 'Noshout'},
 'notell': {'category': 'command',
            'description': 'Toggle blocking of tells from other players.',
            'syntax': 'notell',
            'title': 'Notell'},
 'notick': {'category': 'command',
            'description': 'Alias for tick - toggle tick notifications.',
            'syntax': 'notick',
            'title': 'Notick'},
 'oedit': {'category': 'command',
           'description': 'Online object editor (immortal only).',
           'syntax': 'oedit',
           'title': 'Oedit'},
 'olist': {'category': 'command',
           'description': 'List all objects in a zone (immortal only).\n'
                          '\n'
                          'Usage:\n'
                          '    olist           - List objects in current zone\n'
                          '    olist <zone>    - List objects in specified zone',
           'syntax': 'olist           - List objects in current zone',
           'title': 'Olist'},
 'oload': {'category': 'command',
           'description': 'Load an object into the room or your inventory (immortal only).\n'
                          '\n'
                          'Usage: oload <vnum> [room]',
           'syntax': 'oload <vnum> [room]',
           'title': 'Oload'},
 'open': {'category': 'command',
          'description': 'Open a door or container. Usage: open <door/container>',
          'syntax': 'open <door/container>',
          'title': 'Open'},
 'order': {'category': 'command',
           'description': 'Order your companion or pet. Usage: order <action> [target] OR order <pet> <action> '
                          '[target]',
           'syntax': 'order <action> [target] OR order <pet> <action> [target]',
           'title': 'Order'},
 'overpower': {'category': 'command',
               'description': 'Quick counterattack.',
               'syntax': 'overpower',
               'title': 'Overpower'},
 'paladin': {'category': 'class',
             'description': 'The Paladin class.\n'
                            '\n'
                            'SKILL TREE / PROGRESSION:\n'
                            '- Skills/spells unlock in the order listed for your class.\n'
                            '- Unlock tiers at levels: 2, 3, 5, 7, 10, 15, 20, 25, 30.',
             'title': 'Paladin'},
 'parry': {'category': 'skill',
           'classes': ['warrior'],
           'description': 'Passive chance to deflect attacks when wielding a weapon.',
           'syntax': 'parry',
           'title': 'Parry'},
 'pat': {'category': 'command', 'description': 'Pat someone.', 'syntax': 'pat', 'title': 'Pat'},
 'peace': {'category': 'command',
           'description': 'Stop all combat in the current room (immortal only).\n\nUsage: peace',
           'syntax': 'peace',
           'title': 'Peace'},
 'perform': {'category': 'command',
             'description': '\n'
                            'Begin a bard performance.\n'
                            '\n'
                            'MECHANICS:\n'
                            '- Ongoing song with mana drain\n'
                            '- Moving cancels performance\n',
             'syntax': 'perform',
             'title': 'Perform'},
 'pet': {'category': 'command', 'description': 'Show your pets and companions.', 'syntax': 'pet', 'title': 'Pet'},
 'pets': {'category': 'command',
          'description': 'Manage all your pets. Usage: pets [list|report|assist|recall|dismiss all]',
          'syntax': 'pets [list|report|assist|recall|dismiss all]',
          'title': 'Pets'},
 'pick': {'category': 'command',
          'description': 'Pick a lock (Thief skill). Usage: pick <door/container>',
          'syntax': 'pick <door/container>',
          'title': 'Pick'},
 'pick_lock': {'category': 'skill',
               'classes': ['bard', 'thief'],
               'description': '\n'
                              'Pick locks on doors/containers.\n'
                              '\n'
                              'REQUIREMENTS:\n'
                              '- Lockpick skill\n'
                              '\n'
                              'MECHANICS:\n'
                              '- Skill roll vs difficulty\n'
                              '- Failure leaves lock intact\n',
               'syntax': 'pick_lock',
               'title': 'Pick Lock'},
 'poison': {'category': 'spell',
            'classes': ['necromancer'],
            'description': 'Poison\n'
                           'TARGET: offensive\n'
                           '\n'
                           'CASTING:\n'
                           "- Use `cast 'poison'`.\n"
                           '- Mana cost applies per cast.',
            'level': 1,
            'mana': 25,
            'syntax': "cast 'poison' <target>",
            'title': 'Poison'},
 'poke': {'category': 'command', 'description': 'Poke someone.', 'syntax': 'poke', 'title': 'Poke'},
 'policy': {'category': 'command',
            'description': 'Display server policies and rules.',
            'syntax': 'policy',
            'title': 'Policy'},
 'ponder': {'category': 'command', 'description': 'Ponder.', 'syntax': 'ponder', 'title': 'Ponder'},
 'pour': {'category': 'command',
          'description': 'Pour liquid between containers. Usage: pour <from> <to> OR pour <from> out',
          'syntax': 'pour <from> <to> OR pour <from> out',
          'title': 'Pour'},
 'practice': {'category': 'command',
              'description': 'Practice skills/spells - must be at a guild master for your class.',
              'syntax': 'practice',
              'title': 'Practice'},
 'predators_mark': {'category': 'command',
                    'description': 'Mark a target for increased damage and tracking.',
                    'syntax': 'predators_mark',
                    'title': 'Predators Mark'},
 'preparation': {'category': 'command',
                 'description': 'Reset major cooldowns.',
                 'syntax': 'preparation',
                 'title': 'Preparation'},
 'prompt': {'category': 'command',
            'description': 'Set custom prompt. Usage: prompt <format> or prompt default',
            'syntax': 'prompt <format> or prompt default',
            'title': 'Prompt'},
 'protection_from_evil': {'category': 'spell',
                          'classes': ['cleric', 'mage', 'paladin'],
                          'description': 'Protection from Evil\n'
                                         'TARGET: defensive\n'
                                         '\n'
                                         'CASTING:\n'
                                         "- Use `cast 'protection from evil'`.\n"
                                         '- Mana cost applies per cast.',
                          'level': 1,
                          'mana': 30,
                          'syntax': "cast 'protection from evil'",
                          'title': 'Protection From Evil'},
 'protection_from_good': {'category': 'spell',
                          'classes': ['mage', 'necromancer'],
                          'description': 'Protection from Good\n'
                                         'TARGET: defensive\n'
                                         '\n'
                                         'CASTING:\n'
                                         "- Use `cast 'protection from good'`.\n"
                                         '- Mana cost applies per cast.',
                          'level': 1,
                          'mana': 30,
                          'syntax': "cast 'protection from good'",
                          'title': 'Protection From Good'},
 'pull': {'category': 'command', 'description': 'Pull a lever for lever puzzles.', 'syntax': 'pull', 'title': 'Pull'},
 'purge': {'category': 'command',
           'description': 'Remove all mobs and objects from the room, or a specific target (immortal only).\n'
                          '\n'
                          'Usage: \n'
                          '    purge           - Remove all mobs/objects in room\n'
                          '    purge <target>  - Remove specific mob/object',
           'syntax': 'purge           - Remove all mobs/objects in room',
           'title': 'Purge'},
 'push': {'category': 'command',
          'description': 'Push a symbol or object for puzzle interactions.',
          'syntax': 'push',
          'title': 'Push'},
 'put': {'category': 'command',
         'description': 'Put an item into a container. Usage: put <item> <container> or put all <container>',
         'syntax': 'put <item> <container> or put all <container>',
         'title': 'Put'},
 'qsay': {'category': 'command',
          'description': 'Say something on the quest channel. Usage: qsay <message>',
          'syntax': 'qsay <message>',
          'title': 'Qsay'},
 'quaff': {'category': 'command',
           'description': 'Drink a potion. Usage: quaff <potion>',
           'syntax': 'quaff <potion>',
           'title': 'Quaff'},
 'quest': {'category': 'command', 'description': 'Manage quests.', 'syntax': 'quest', 'title': 'Quest'},
 'questlog': {'category': 'command',
              'description': 'Show quest log (alias for quest log).',
              'syntax': 'questlog',
              'title': 'Questlog'},
 'quit': {'category': 'command', 'description': 'Quit the game.', 'syntax': 'quit', 'title': 'Quit'},
 'rage': {'category': 'command', 'description': 'Display current rage level.', 'syntax': 'rage', 'title': 'Rage'},
 'raise': {'category': 'command',
           'description': 'Raise a necromancer servant. Usage: raise <knight|wraith|lich|stalker>',
           'syntax': 'raise <knight|wraith|lich|stalker>',
           'title': 'Raise'},
 'rampage': {'category': 'command',
             'description': 'Attack all enemies in the room.',
             'syntax': 'rampage',
             'title': 'Rampage'},
 'ranger': {'category': 'class',
            'description': 'The Ranger class.\n'
                           '\n'
                           'SKILL TREE / PROGRESSION:\n'
                           '- Skills/spells unlock in the order listed for your class.\n'
                           '- Unlock tiers at levels: 2, 3, 5, 7, 10, 15, 20, 25, 30.',
            'title': 'Ranger'},
 'rapid_shot': {'category': 'command',
                'description': 'Fire multiple arrows in quick succession.',
                'syntax': 'rapid_shot',
                'title': 'Rapid Shot'},
 'read': {'category': 'command',
          'description': 'Read a book, scroll, or readable item.',
          'syntax': 'read',
          'title': 'Read'},
 'recall': {'category': 'command',
            'description': 'Recall to your recall point (temple).\n'
                           '\n'
                           'Usage:\n'
                           '    recall     - Teleport to your recall point\n'
                           '    recall set - Set current location as recall point',
            'syntax': 'recall     - Teleport to your recall point',
            'title': 'Recall'},
 'recite': {'category': 'command',
            'description': 'Read a scroll. Usage: recite <scroll> [target]',
            'syntax': 'recite <scroll> [target]',
            'title': 'Recite'},
 'redit': {'category': 'command',
           'description': 'Online room editor (immortal only).',
           'syntax': 'redit',
           'title': 'Redit'},
 'relight': {'category': 'command',
             'description': 'Relight your light source. Usage: relight light',
             'syntax': 'relight light',
             'title': 'Relight'},
 'remove': {'category': 'command',
            'description': "Remove worn equipment or 'remove all' to remove everything.",
            'syntax': 'remove',
            'title': 'Remove'},
 'remove_curse': {'category': 'spell',
                  'classes': ['cleric'],
                  'description': 'Remove Curse\n'
                                 'TARGET: defensive\n'
                                 '\n'
                                 'CASTING:\n'
                                 "- Use `cast 'remove curse'`.\n"
                                 '- Mana cost applies per cast.',
                  'level': 1,
                  'mana': 35,
                  'syntax': "cast 'remove curse'",
                  'title': 'Remove Curse'},
 'remove_poison': {'category': 'spell',
                   'classes': ['cleric'],
                   'description': 'Remove Poison\n'
                                  'TARGET: defensive\n'
                                  '\n'
                                  'CASTING:\n'
                                  "- Use `cast 'remove poison'`.\n"
                                  '- Mana cost applies per cast.',
                   'level': 1,
                   'mana': 30,
                   'syntax': "cast 'remove poison'",
                   'title': 'Remove Poison'},
 'rend': {'category': 'command', 'description': 'Apply a bleeding wound.', 'syntax': 'rend', 'title': 'Rend'},
 'rent': {'category': 'command',
          'description': 'Rent a room at the Inn to save your character and quit safely.',
          'syntax': 'rent',
          'title': 'Rent'},
 'report': {'category': 'command',
            'description': 'Report your status to the group.',
            'syntax': 'report',
            'title': 'Report'},
 'reputation': {'category': 'command',
                'description': 'Show reputation standings with all factions.',
                'syntax': 'reputation',
                'title': 'Reputation'},
 'rescue': {'category': 'skill',
            'classes': ['paladin', 'warrior'],
            'description': '\n'
                           'Rescue an ally by pulling aggro.\n'
                           '\n'
                           'MECHANICS:\n'
                           '- Success based on skill and level\n'
                           '- On success: target switches to you\n',
            'syntax': 'rescue',
            'title': 'Rescue'},
 'rest': {'category': 'command', 'description': 'Rest to regenerate faster.', 'syntax': 'rest', 'title': 'Rest'},
 'restore': {'category': 'command',
             'description': 'Fully restore HP/mana/move for self or a target (immortal only).\n'
                            '\n'
                            'Usage:\n'
                            '    restore         - Restore yourself\n'
                            '    restore <name>  - Restore a player',
             'syntax': 'restore         - Restore yourself',
             'title': 'Restore'},
 'resurrect': {'category': 'spell',
               'classes': ['cleric'],
               'description': 'Resurrect\n'
                              'TARGET: special\n'
                              '\n'
                              'CASTING:\n'
                              "- Use `cast 'resurrect'`.\n"
                              '- Mana cost applies per cast.',
               'level': 1,
               'mana': 150,
               'syntax': "cast 'resurrect'",
               'title': 'Resurrect'},
 'retrieve': {'category': 'command',
              'description': 'Retrieve an item from your house. Usage: retrieve <item>',
              'syntax': 'retrieve <item>',
              'title': 'Retrieve'},
 'righteous_fury': {'category': 'spell',
                    'classes': ['cleric'],
                    'description': 'Righteous Fury\n'
                                   'TARGET: self\n'
                                   '\n'
                                   'CASTING:\n'
                                   "- Use `cast 'righteous fury'`.\n"
                                   '- Mana cost applies per cast.',
                    'level': 1,
                    'mana': 55,
                    'syntax': "cast 'righteous fury'",
                    'title': 'Righteous Fury'},
 'ritual': {'category': 'command',
            'description': 'Perform dark ritual to empower all undead pets (Necromancer only).',
            'syntax': 'ritual',
            'title': 'Ritual'},
 'rlist': {'category': 'command',
           'description': 'List all rooms in a zone (immortal only).\n'
                          '\n'
                          'Usage:\n'
                          '    rlist           - List rooms in current zone\n'
                          '    rlist <zone>    - List rooms in specified zone',
           'syntax': 'rlist           - List rooms in current zone',
           'title': 'Rlist'},
 'sacred_shield': {'category': 'command',
                   'description': 'Apply a holy shield.',
                   'syntax': 'sacred_shield',
                   'title': 'Sacred Shield'},
 'sacrifice': {'category': 'command',
               'description': 'Sacrifice a corpse to the gods for gold.',
               'syntax': 'sacrifice',
               'title': 'Sacrifice'},
 'salute': {'category': 'command', 'description': 'Salute.', 'syntax': 'salute', 'title': 'Salute'},
 'sanctuary': {'category': 'spell',
               'classes': ['cleric'],
               'description': '\n'
                              'Holy aura that reduces incoming damage.\n'
                              '\n'
                              'MECHANICS:\n'
                              '- Percentage damage reduction\n'
                              '- Strong defensive buff\n',
               'level': 1,
               'mana': 75,
               'syntax': "cast 'sanctuary'",
               'title': 'Sanctuary'},
 'save': {'category': 'command', 'description': 'Save your character.', 'syntax': 'save', 'title': 'Save'},
 'say': {'category': 'command', 'description': 'Say something to the room.', 'syntax': 'say', 'title': 'Say'},
 'scan': {'category': 'skill',
          'classes': ['ranger'],
          'description': 'Scan for creatures in adjacent rooms.\n'
                         '\n'
                         'TRAINING:\n'
                         '- Use PRACTICE at your class trainer.\n'
                         '- Max 85% skill cap.',
          'syntax': 'scan',
          'title': 'Scan'},
 'score': {'category': 'command', 'description': 'Show player stats.', 'syntax': 'score', 'title': 'Score'},
 'scribe': {'category': 'skill',
            'classes': ['mage'],
            'description': 'A class skill. Use it to gain tactical advantages in combat or utility.\n'
                           '\n'
                           'TRAINING:\n'
                           '- Use PRACTICE at your class trainer.\n'
                           '- Max 85% skill cap.',
            'syntax': 'scribe',
            'title': 'Scribe'},
 'seal_of_command': {'category': 'command',
                     'description': 'Empower attacks with holy damage.',
                     'syntax': 'seal_of_command',
                     'title': 'Seal Of Command'},
 'search': {'category': 'command',
            'description': 'Search the room for hidden exits or items.',
            'syntax': 'search',
            'title': 'Search'},
 'second_attack': {'category': 'skill',
                   'classes': ['assassin', 'paladin', 'ranger', 'thief', 'warrior'],
                   'description': 'A class skill. Use it to gain tactical advantages in combat or utility.\n'
                                  '\n'
                                  'TRAINING:\n'
                                  '- Use PRACTICE at your class trainer.\n'
                                  '- Max 85% skill cap.',
                   'syntax': 'second_attack',
                   'title': 'Second Attack'},
 'sell': {'category': 'command',
          'description': 'Sell an item to a shop. Usage: sell <item>',
          'syntax': 'sell <item>',
          'title': 'Sell'},
 'set': {'category': 'command',
         'description': 'Set a field on a player or mob (immortal only).\n'
                        '\n'
                        'Usage: set <target> <field> <value>\n'
                        '\n'
                        'Fields for characters:\n'
                        '    level, hp, maxhp, mana, maxmana, move, maxmove\n'
                        '    str, int, wis, dex, con, cha\n'
                        '    gold, exp, alignment, hitroll, damroll, ac',
         'syntax': 'set <target> <field> <value>',
         'title': 'Set'},
 'sets': {'category': 'command', 'description': 'Show active zone set bonuses.', 'syntax': 'sets', 'title': 'Sets'},
 'settings': {'category': 'command',
              'description': 'Show toggleable settings.',
              'syntax': 'settings',
              'title': 'Settings'},
 'shadow_blade': {'category': 'command',
                  'description': 'Empower attacks from stealth.',
                  'syntax': 'shadow_blade',
                  'title': 'Shadow Blade'},
 'shadow_blink': {'category': 'command',
                  'description': 'Blink behind target and stealth briefly.',
                  'syntax': 'shadow_blink',
                  'title': 'Shadow Blink'},
 'shadow_dance': {'category': 'command',
                  'description': 'Use stealth abilities in combat for a short time.',
                  'syntax': 'shadow_dance',
                  'title': 'Shadow Dance'},
 'shadow_step': {'category': 'skill',
                 'classes': ['assassin'],
                 'description': '\n'
                                'Step through shadows to reposition for a strike.\n'
                                '\n'
                                'REQUIREMENTS:\n'
                                '- Must see the target\n'
                                '\n'
                                'MECHANICS:\n'
                                '- Teleports behind target (flavor)\n'
                                '- Improves next attack accuracy\n',
                 'syntax': 'shadow_step',
                 'title': 'Shadow Step'},
 'shadowstep': {'category': 'command',
                'description': 'Step through shadows behind target.',
                'syntax': 'shadowstep',
                'title': 'Shadowstep'},
 'shield': {'category': 'spell',
            'classes': ['mage', 'necromancer'],
            'description': 'Shield\n'
                           'TARGET: defensive\n'
                           '\n'
                           'CASTING:\n'
                           "- Use `cast 'shield'`.\n"
                           '- Mana cost applies per cast.',
            'level': 1,
            'mana': 25,
            'syntax': "cast 'shield'",
            'title': 'Shield'},
 'shield_bash': {'category': 'command',
                 'description': '\n'
                                'Bash with a shield to stun/knock down.\n'
                                '\n'
                                'REQUIREMENTS:\n'
                                '- Shield equipped\n'
                                '\n'
                                'MECHANICS:\n'
                                '- Higher success with STR\n'
                                '- Stuns briefly on success\n',
                 'syntax': 'shield_bash',
                 'title': 'Shield Bash'},
 'shield_block': {'category': 'skill',
                  'classes': ['warrior'],
                  'description': 'Passive chance to block attacks with a shield.',
                  'syntax': 'shield_block',
                  'title': 'Shield Block'},
 'shield_of_faith': {'category': 'spell',
                     'classes': ['cleric', 'paladin'],
                     'description': 'Shield of Faith\n'
                                    'TARGET: defensive\n'
                                    '\n'
                                    'CASTING:\n'
                                    "- Use `cast 'shield of faith'`.\n"
                                    '- Mana cost applies per cast.',
                     'level': 1,
                     'mana': 35,
                     'syntax': "cast 'shield of faith'",
                     'title': 'Shield Of Faith'},
 'shield_wall': {'category': 'command',
                 'description': 'Reduce incoming damage for a short time.',
                 'syntax': 'shield_wall',
                 'title': 'Shield Wall'},
 'shout': {'category': 'command', 'description': 'Shout to everyone in the zone.', 'syntax': 'shout', 'title': 'Shout'},
 'show': {'category': 'command',
          'description': 'Show various game statistics (immortal only).\n'
                         '\n'
                         'Usage:\n'
                         '    show zones    - List all zones\n'
                         '    show players  - List all online players with details\n'
                         '    show stats    - Show server statistics',
          'syntax': 'show zones    - List all zones',
          'title': 'Show'},
 'shrug': {'category': 'command', 'description': 'Shrug.', 'syntax': 'shrug', 'title': 'Shrug'},
 'shutdown': {'category': 'command',
              'description': 'Shutdown the MUD server (immortal only).\n\nUsage: shutdown [now|reboot]',
              'syntax': 'shutdown [now|reboot]',
              'title': 'Shutdown'},
 'sigh': {'category': 'command', 'description': 'Sigh.', 'syntax': 'sigh', 'title': 'Sigh'},
 'silence_strike': {'category': 'command',
                    'description': 'Strike and silence spellcasting.',
                    'syntax': 'silence_strike',
                    'title': 'Silence Strike'},
 'sit': {'category': 'command', 'description': 'Sit down.', 'syntax': 'sit', 'title': 'Sit'},
 'skill': {'category': 'command', 'description': 'Alias for skills command.', 'syntax': 'skill', 'title': 'Skill'},
 'skills': {'category': 'command',
            'description': 'Show all skills and spells available to your class, or pet abilities.',
            'syntax': 'skills',
            'title': 'Skills'},
 'slap': {'category': 'command', 'description': 'Slap someone.', 'syntax': 'slap', 'title': 'Slap'},
 'slay': {'category': 'command',
          'description': 'Instantly kill a target (immortal only).\n\nUsage: slay <target>',
          'syntax': 'slay <target>',
          'title': 'Slay'},
 'sleep': {'category': 'spell',
           'classes': ['bard', 'mage'],
           'description': "Sleep\nTARGET: offensive\n\nCASTING:\n- Use `cast 'sleep'`.\n- Mana cost applies per cast.",
           'level': 1,
           'mana': 20,
           'syntax': "cast 'sleep' <target>",
           'title': 'Sleep'},
 'slicedice': {'category': 'command',
               'description': 'DoT finisher that uses 3+ combo points.',
               'syntax': 'slicedice',
               'title': 'Slicedice'},
 'slip_away': {'category': 'command',
               'description': 'Enter stealth after a dodge.',
               'syntax': 'slip_away',
               'title': 'Slip Away'},
 'slow': {'category': 'spell',
          'classes': ['bard'],
          'description': "Slow\nTARGET: offensive\n\nCASTING:\n- Use `cast 'slow'`.\n- Mana cost applies per cast.",
          'level': 1,
          'mana': 35,
          'syntax': "cast 'slow' <target>",
          'title': 'Slow'},
 'smile': {'category': 'command', 'description': 'Smile at someone.', 'syntax': 'smile', 'title': 'Smile'},
 'smite': {'category': 'skill',
           'classes': ['paladin'],
           'description': '\n'
                          'Paladin holy strike.\n'
                          '\n'
                          'MECHANICS:\n'
                          '- Bonus damage vs undead/evil\n'
                          '- Uses holy_smite bonus where available\n',
           'syntax': 'smite',
           'title': 'Smite'},
 'sneak': {'category': 'skill',
           'classes': ['assassin', 'bard', 'ranger', 'thief'],
           'description': '\n'
                          'Move silently and avoid detection.\n'
                          '\n'
                          'MECHANICS:\n'
                          '- Persists until a failed movement check\n'
                          '- Detection vs mobs uses your stealth vs mob detect + environment\n'
                          '- Light penalizes stealth; dark/forest/swamp boosts it\n'
                          '\n'
                          'TIPS:\n'
                          '- Pair with Hide for best results\n'
                          '- Cover/snuff light to reduce penalties\n',
           'syntax': 'sneak',
           'title': 'Sneak'},
 'snicker': {'category': 'command', 'description': 'Snicker.', 'syntax': 'snicker', 'title': 'Snicker'},
 'snoop': {'category': 'command',
           'description': 'Watch what another player sees (immortal only).\n'
                          '\n'
                          'Usage:\n'
                          '    snoop <player>  - Start snooping on a player\n'
                          '    snoop           - Stop snooping',
           'syntax': 'snoop <player>  - Start snooping on a player',
           'title': 'Snoop'},
 'snuff': {'category': 'command',
           'description': 'Snuff your light source. Usage: snuff light',
           'syntax': 'snuff light',
           'title': 'Snuff'},
 'social': {'category': 'command', 'description': 'Process a social command.', 'syntax': 'social', 'title': 'Social'},
 'socials': {'category': 'command',
             'description': 'List all available social commands.',
             'syntax': 'socials',
             'title': 'Socials'},
 'songs': {'category': 'command',
           'description': '\n'
                          'List available bard songs and performance status.\n'
                          '\n'
                          'MECHANICS:\n'
                          '- Songs are ongoing buffs/debuffs\n'
                          '- Mana drains each tick while active\n',
           'syntax': 'songs',
           'title': 'Songs'},
 'soulstone': {'category': 'command',
               'description': 'Create a necromancer soulstone. Usage: soulstone [create]',
               'syntax': 'soulstone [create]',
               'title': 'Soulstone'},
 'south': {'category': 'command',
           'description': 'No additional details available yet.',
           'syntax': 'south',
           'title': 'South'},
 'spell_reflection': {'category': 'spell',
                      'classes': ['mage'],
                      'description': 'Spell Reflection\n'
                                     'TARGET: self\n'
                                     '\n'
                                     'CASTING:\n'
                                     "- Use `cast 'spell reflection'`.\n"
                                     '- Mana cost applies per cast.',
                      'level': 1,
                      'mana': 70,
                      'syntax': "cast 'spell reflection'",
                      'title': 'Spell Reflection'},
 'spells': {'category': 'command', 'description': 'Show known spells.', 'syntax': 'spells', 'title': 'Spells'},
 'split': {'category': 'command',
           'description': 'Split gold with your group. Usage: split <amount>',
           'syntax': 'split <amount>',
           'title': 'Split'},
 'stable': {'category': 'command',
            'description': 'Stable services. Usage: stable [list|buy <mount>]',
            'syntax': 'stable [list|buy <mount>]',
            'title': 'Stable'},
 'stampede': {'category': 'command',
              'description': 'Command all pets to attack.',
              'syntax': 'stampede',
              'title': 'Stampede'},
 'stance': {'category': 'command',
            'description': 'Switch warrior combat stance.',
            'syntax': 'stance',
            'title': 'Stance'},
 'stand': {'category': 'command', 'description': 'Stand up.', 'syntax': 'stand', 'title': 'Stand'},
 'stat': {'category': 'command',
          'description': 'View detailed stats on a player, mob, or object (immortal only).\n\nUsage: stat <target>',
          'syntax': 'stat <target>',
          'title': 'Stat'},
 'steal': {'category': 'skill',
           'classes': ['thief'],
           'description': '\n'
                          'Attempt to steal gold from a target.\n'
                          '\n'
                          'REQUIREMENTS:\n'
                          '- Must be out of combat\n'
                          '\n'
                          'MECHANICS:\n'
                          '- DEX vs target DEX check\n'
                          '- Failure may anger the target\n',
           'syntax': 'steal',
           'title': 'Steal'},
 'stoneskin': {'category': 'spell',
               'classes': ['mage'],
               'description': 'Stoneskin\n'
                              'TARGET: defensive\n'
                              '\n'
                              'CASTING:\n'
                              "- Use `cast 'stoneskin'`.\n"
                              '- Mana cost applies per cast.',
               'level': 1,
               'mana': 60,
               'syntax': "cast 'stoneskin'",
               'title': 'Stoneskin'},
 'stop': {'category': 'command',
          'description': 'Stop the current bard performance.',
          'syntax': 'stop',
          'title': 'Stop'},
 'storage': {'category': 'command',
             'description': 'View items in your storage locker.',
             'syntax': 'storage',
             'title': 'Storage'},
 'store': {'category': 'command',
           'description': 'Store an item in your house. Usage: store <item>',
           'syntax': 'store <item>',
           'title': 'Store'},
 'story': {'category': 'command',
           'description': 'Show main story quest progress.',
           'syntax': 'story',
           'title': 'Story'},
 'summon': {'category': 'spell',
            'classes': ['cleric'],
            'description': "Summon\nTARGET: special\n\nCASTING:\n- Use `cast 'summon'`.\n- Mana cost applies per cast.",
            'level': 1,
            'mana': 75,
            'syntax': "cast 'summon'",
            'title': 'Summon'},
 'sunder_armor': {'category': 'command',
                  'description': 'Reduce target armor temporarily.',
                  'syntax': 'sunder_armor',
                  'title': 'Sunder Armor'},
 'take': {'category': 'command', 'description': 'Alias for get.', 'syntax': 'take', 'title': 'Take'},
 'talents': {'category': 'command',
             'description': 'View and spend talent points.\n'
                            '\n'
                            'Usage:\n'
                            '    talents           - Show all talent trees\n'
                            "    talents <tree>    - Show specific tree (e.g., 'talents fury')\n"
                            '    talents learn <id> - Learn/rank up a talent\n'
                            '    talents reset     - Reset all talents (costs gold)',
             'syntax': 'talents           - Show all talent trees',
             'title': 'Talents'},
 'talk': {'category': 'command', 'description': 'Talk to an NPC.', 'syntax': 'talk', 'title': 'Talk'},
 'tame': {'category': 'skill',
          'classes': ['ranger'],
          'description': 'Tame a wild creature. Usage: tame <creature>\n'
                         '\n'
                         'TRAINING:\n'
                         '- Use PRACTICE at your class trainer.\n'
                         '- Max 85% skill cap.',
          'syntax': 'tame',
          'title': 'Tame'},
 'target': {'category': 'command', 'description': 'Set your combat target.', 'syntax': 'target', 'title': 'Target'},
 'taste': {'category': 'command',
           'description': 'Taste food or drink. Usage: taste <item>',
           'syntax': 'taste <item>',
           'title': 'Taste'},
 'teleport': {'category': 'spell',
              'classes': ['mage'],
              'description': '\n'
                             'Teleport to a random safe location.\n'
                             '\n'
                             'MECHANICS:\n'
                             '- Random destination\n'
                             '- Cannot use in no‑teleport rooms\n',
              'level': 1,
              'mana': 50,
              'syntax': "cast 'teleport'",
              'title': 'Teleport'},
 'tell': {'category': 'command', 'description': 'Send a private message.', 'syntax': 'tell', 'title': 'Tell'},
 'thank': {'category': 'command', 'description': 'Thank someone.', 'syntax': 'thank', 'title': 'Thank'},
 'thief': {'category': 'class',
           'description': 'The Thief class.\n'
                          '\n'
                          'SKILL TREE / PROGRESSION:\n'
                          '- Skills/spells unlock in the order listed for your class.\n'
                          '- Unlock tiers at levels: 2, 3, 5, 7, 10, 15, 20, 25, 30.',
           'title': 'Thief'},
 'third_attack': {'category': 'skill',
                  'classes': ['warrior'],
                  'description': 'A class skill. Use it to gain tactical advantages in combat or utility.\n'
                                 '\n'
                                 'TRAINING:\n'
                                 '- Use PRACTICE at your class trainer.\n'
                                 '- Max 85% skill cap.',
                  'syntax': 'third_attack',
                  'title': 'Third Attack'},
 'tick': {'category': 'command',
          'description': 'Toggle tick timer notifications.\n'
                         '\n'
                         'Shows when game ticks happen (regen, combat, etc.)\n'
                         '\n'
                         'Usage:\n'
                         '    tick         - Toggle tick notifications\n'
                         '    tick on      - Turn on\n'
                         '    tick off     - Turn off',
          'syntax': 'tick         - Toggle tick notifications',
          'title': 'Tick'},
 'tickle': {'category': 'command', 'description': 'Tickle someone.', 'syntax': 'tickle', 'title': 'Tickle'},
 'time': {'category': 'command', 'description': 'Display the current game time.', 'syntax': 'time', 'title': 'Time'},
 'time_old': {'category': 'command',
              'description': 'Show the current in-game time (old version).',
              'syntax': 'time_old',
              'title': 'Time Old'},
 'title': {'category': 'command',
           'description': 'Set your title. Usage: title <new title>',
           'syntax': 'title <new title>',
           'title': 'Title'},
 'toggle': {'category': 'command', 'description': 'Show all toggle settings.', 'syntax': 'toggle', 'title': 'Toggle'},
 'track': {'category': 'skill',
           'classes': ['ranger'],
           'description': '\n'
                          'Track a target through the wilderness.\n'
                          '\n'
                          'MECHANICS:\n'
                          '- WIS/DEX vs target stealth\n'
                          '- Best outdoors\n',
           'syntax': 'track',
           'title': 'Track'},
 'transfer': {'category': 'command',
              'description': 'Teleport a player to your location (immortal only).\n\nUsage: transfer <player>',
              'syntax': 'transfer <player>',
              'title': 'Transfer'},
 'travel': {'category': 'command',
            'description': 'Travel to a discovered waypoint.\n\nUsage:\n    travel <waypoint>',
            'syntax': 'travel <waypoint>',
            'title': 'Travel'},
 'trip': {'category': 'skill',
          'classes': ['thief'],
          'description': 'Knock a target down with a leg sweep.',
          'syntax': 'trip',
          'title': 'Trip'},
 'tumble': {'category': 'skill',
            'classes': ['thief'],
            'description': 'Short evasive window reducing incoming damage.',
            'syntax': 'tumble',
            'title': 'Tumble'},
 'turn_undead': {'category': 'skill',
                 'classes': ['cleric', 'paladin'],
                 'description': '\n'
                                'Turn or repel undead creatures.\n'
                                '\n'
                                'MECHANICS:\n'
                                '- WIS + skill roll vs undead level\n'
                                '- On success: undead flee\n',
                 'syntax': 'turn_undead',
                 'title': 'Turn Undead'},
 'turnundead': {'category': 'command',
                'description': 'Turn undead creatures, causing fear or destroying weak ones.',
                'syntax': 'turnundead',
                'title': 'Turnundead'},
 'typo': {'category': 'command',
          'description': 'Report a typo. Usage: typo <description>',
          'syntax': 'typo <description>',
          'title': 'Typo'},
 'unalias': {'category': 'command', 'description': 'Remove a personal alias.', 'syntax': 'unalias', 'title': 'Unalias'},
 'uncover': {'category': 'command',
             'description': 'Uncover your light source. Usage: uncover light',
             'syntax': 'uncover light',
             'title': 'Uncover'},
 'ungroup': {'category': 'command',
             'description': 'Leave your group or remove someone from it.\n'
                            '\n'
                            'Usage:\n'
                            '    ungroup         - Leave your current group\n'
                            '    ungroup <name>  - Remove player from group (leader only)',
             'syntax': 'ungroup         - Leave your current group',
             'title': 'Ungroup'},
 'unlabel': {'category': 'command', 'description': 'Remove a target label.', 'syntax': 'unlabel', 'title': 'Unlabel'},
 'unlock': {'category': 'command',
            'description': 'Unlock a door or container. Usage: unlock <door/container>',
            'syntax': 'unlock <door/container>',
            'title': 'Unlock'},
 'up': {'category': 'command', 'description': 'No additional details available yet.', 'syntax': 'up', 'title': 'Up'},
 'updates': {'category': 'command',
             'description': 'Show recent game updates and changes. Usage: updates [number of days]',
             'syntax': 'updates [number of days]',
             'title': 'Updates'},
 'value': {'category': 'command',
           'description': 'Check how much a shop will pay for an item. Usage: value <item>',
           'syntax': 'value <item>',
           'title': 'Value'},
 'vampiric_touch': {'category': 'spell',
                    'classes': ['necromancer'],
                    'description': '\nDrain life from a target.\n\nMECHANICS:\n- Deals damage and heals you\n',
                    'level': 1,
                    'mana': 30,
                    'syntax': "cast 'vampiric touch' <target>",
                    'title': 'Vampiric Touch'},
 'vanish': {'category': 'command',
            'description': 'Instant stealth and drop threat.',
            'syntax': 'vanish',
            'title': 'Vanish'},
 'vendetta': {'category': 'command',
              'description': 'Mark target to take extra damage from you.',
              'syntax': 'vendetta',
              'title': 'Vendetta'},
 'visible': {'category': 'command',
             'description': 'Come out of hiding or stop sneaking.',
             'syntax': 'visible',
             'title': 'Visible'},
 'volley': {'category': 'command',
            'description': 'Rain arrows on all enemies in the room.',
            'syntax': 'volley',
            'title': 'Volley'},
 'wake': {'category': 'command', 'description': 'Wake up.', 'syntax': 'wake', 'title': 'Wake'},
 'warcry': {'category': 'command',
            'description': 'Terrifying shout that fears enemies and buffs allies.',
            'syntax': 'warcry',
            'title': 'Warcry'},
 'warrior': {'category': 'class',
             'description': 'The Warrior class.\n'
                            '\n'
                            'SKILL TREE / PROGRESSION:\n'
                            '- Skills/spells unlock in the order listed for your class.\n'
                            '- Unlock tiers at levels: 2, 3, 5, 7, 10, 15, 20, 25, 30.',
             'title': 'Warrior'},
 'wave': {'category': 'command', 'description': 'Wave.', 'syntax': 'wave', 'title': 'Wave'},
 'waypoints': {'category': 'command',
               'description': 'List discovered waypoints.',
               'syntax': 'waypoints',
               'title': 'Waypoints'},
 'weaken': {'category': 'spell',
            'classes': ['necromancer'],
            'description': 'Weaken\n'
                           'TARGET: offensive\n'
                           '\n'
                           'CASTING:\n'
                           "- Use `cast 'weaken'`.\n"
                           '- Mana cost applies per cast.',
            'level': 1,
            'mana': 20,
            'syntax': "cast 'weaken' <target>",
            'title': 'Weaken'},
 'wear': {'category': 'command',
          'description': "Wear an item or 'wear all' to wear everything you can.",
          'syntax': 'wear',
          'title': 'Wear'},
 'weather': {'category': 'command',
             'description': 'Check the current weather.',
             'syntax': 'weather',
             'title': 'Weather'},
 'west': {'category': 'command',
          'description': 'No additional details available yet.',
          'syntax': 'west',
          'title': 'West'},
 'where': {'category': 'command', 'description': 'Show where players/mobs are.', 'syntax': 'where', 'title': 'Where'},
 'who': {'category': 'command', 'description': 'Show online players.', 'syntax': 'who', 'title': 'Who'},
 'wield': {'category': 'command', 'description': 'Wield a weapon.', 'syntax': 'wield', 'title': 'Wield'},
 'wimpy': {'category': 'command',
           'description': 'Set auto-flee HP threshold. Usage: wimpy [hp amount]',
           'syntax': 'wimpy [hp amount]',
           'title': 'Wimpy'},
 'wink': {'category': 'command', 'description': 'Wink.', 'syntax': 'wink', 'title': 'Wink'},
 'withdraw': {'category': 'command',
              'description': 'Withdraw gold from the bank. Usage: withdraw <amount>',
              'syntax': 'withdraw <amount>',
              'title': 'Withdraw'},
 'wizhelp': {'category': 'command',
             'description': 'List all immortal commands.\n\nUsage: wizhelp',
             'syntax': 'wizhelp',
             'title': 'Wizhelp'},
 'wizinvis': {'category': 'command',
              'description': 'Toggle invisibility to mortals (immortal only).\n\nUsage: wizinvis [level]',
              'syntax': 'wizinvis [level]',
              'title': 'Wizinvis'},
 'word_of_recall': {'category': 'spell',
                    'classes': ['cleric'],
                    'description': 'Word of Recall\n'
                                   'TARGET: self\n'
                                   '\n'
                                   'CASTING:\n'
                                   "- Use `cast 'word of recall'`.\n"
                                   '- Mana cost applies per cast.',
                    'level': 1,
                    'mana': 15,
                    'syntax': "cast 'word of recall'",
                    'title': 'Word Of Recall'},
 'worth': {'category': 'command',
           'description': 'Show your total wealth breakdown.\n\nUsage: worth',
           'syntax': 'worth',
           'title': 'Worth'},
 'wyvern_sting': {'category': 'command',
                  'description': 'Put target to sleep briefly.',
                  'syntax': 'wyvern_sting',
                  'title': 'Wyvern Sting'},
 'xp': {'category': 'command', 'description': 'Show XP breakdown and progress.', 'syntax': 'xp', 'title': 'Xp'},
 'yawn': {'category': 'command', 'description': 'Yawn.', 'syntax': 'yawn', 'title': 'Yawn'},
 'zreset': {'category': 'command',
            'description': 'Reset (repopulate) a zone (immortal only).\n'
                           '\n'
                           'Usage: \n'
                           '    zreset          - Reset current zone\n'
                           '    zreset <number> - Reset specific zone',
            'syntax': 'zreset          - Reset current zone',
            'title': 'Zreset'},

 # ========== LEVEL 31-60 ABILITIES ==========
 # These powerful abilities unlock at higher levels and define endgame play.

 # ----- WARRIOR LEVEL 31-60 -----
 'rallying_cry': {
     'category': 'skill',
     'classes': ['warrior'],
     'title': 'Rallying Cry',
     'description': 'Let out a rallying cry that buffs the entire party with increased max HP and regeneration.\n\n'
                    'MECHANICS:\n'
                    '- Increases max HP for all group members\n'
                    '- Lasts 30 seconds\n'
                    '- 2 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Warrior class\n'
                    '- Level 32\n',
     'syntax': 'rallying_cry',
     'level': 32,
     'cooldown': 120,
 },
 'shattering_blow': {
     'category': 'skill',
     'classes': ['warrior'],
     'title': 'Shattering Blow',
     'description': 'Strike with such force that the target\'s armor is reduced.\n\n'
                    'MECHANICS:\n'
                    '- Deals heavy damage\n'
                    '- Reduces target\'s armor for 20 seconds\n'
                    '- 15 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Warrior class\n'
                    '- Level 38\n',
     'syntax': 'shattering_blow [target]',
     'level': 38,
     'cooldown': 15,
 },
 'commanding_shout': {
     'category': 'skill',
     'classes': ['warrior'],
     'title': 'Commanding Shout',
     'description': 'Let out a commanding shout that taunts all enemies in the room.\n\n'
                    'MECHANICS:\n'
                    '- Forces all enemies to attack you\n'
                    '- Taunt lasts 12 seconds\n'
                    '- 30 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Warrior class\n'
                    '- Level 44\n',
     'syntax': 'commanding_shout',
     'level': 44,
     'cooldown': 30,
 },
 'heroic_leap': {
     'category': 'skill',
     'classes': ['warrior'],
     'title': 'Heroic Leap',
     'description': 'Leap to a target, dealing damage and stunning them.\n\n'
                    'MECHANICS:\n'
                    '- Gap closer - use to engage from range\n'
                    '- Stuns target for 6 seconds\n'
                    '- 45 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Warrior class\n'
                    '- Level 50\n',
     'syntax': 'heroic_leap <target>',
     'level': 50,
     'cooldown': 45,
 },
 'warpath': {
     'category': 'skill',
     'classes': ['warrior'],
     'title': 'Warpath',
     'description': 'Enter a sustained damage mode where all attacks deal increased damage.\n\n'
                    'MECHANICS:\n'
                    '- +15 damage and haste for 40 seconds\n'
                    '- 3 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Warrior class\n'
                    '- Level 56\n',
     'syntax': 'warpath',
     'level': 56,
     'cooldown': 180,
 },
 'titans_wrath': {
     'category': 'skill',
     'classes': ['warrior'],
     'title': "Titan's Wrath",
     'description': 'CAPSTONE ABILITY: Invoke the power of a titan for 10 seconds of god mode.\n\n'
                    'MECHANICS:\n'
                    '- IMMUNE to all damage\n'
                    '- Double damage on all attacks\n'
                    '- Attacks cleave to all enemies\n'
                    '- 10 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Warrior class\n'
                    '- Level 60\n',
     'syntax': 'titans_wrath',
     'level': 60,
     'cooldown': 600,
 },

 # ----- MAGE LEVEL 31-60 -----
 'time_warp': {
     'category': 'spell',
     'classes': ['mage'],
     'title': 'Time Warp',
     'description': 'Bend the fabric of time, granting haste to you and your party.\n\n'
                    'MECHANICS:\n'
                    '- Haste + hit/damage bonus for whole group\n'
                    '- 40 second duration\n'
                    '- 5 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Mage class\n'
                    '- Level 38\n',
     'syntax': "cast 'time warp'",
     'level': 38,
     'mana': 120,
     'cooldown': 300,
 },
 'arcane_explosion': {
     'category': 'spell',
     'classes': ['mage'],
     'title': 'Arcane Explosion',
     'description': 'Unleash a massive arcane explosion that damages all enemies in the room.\n\n'
                    'MECHANICS:\n'
                    '- Massive AoE damage\n'
                    '- 30 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Mage class\n'
                    '- Level 44\n',
     'syntax': "cast 'arcane explosion'",
     'level': 44,
     'mana': 80,
     'cooldown': 30,
 },
 'icy_veins': {
     'category': 'spell',
     'classes': ['mage'],
     'title': 'Icy Veins',
     'description': 'Channel frost power for increased crit chance and cast speed.\n\n'
                    'MECHANICS:\n'
                    '- +30% crit chance\n'
                    '- Haste effect\n'
                    '- +15 spell power\n'
                    '- 30 second duration\n'
                    '- 3 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Mage class\n'
                    '- Level 50\n',
     'syntax': "cast 'icy veins'",
     'level': 50,
     'mana': 100,
     'cooldown': 180,
 },
 'combustion_master': {
     'category': 'spell',
     'classes': ['mage'],
     'title': 'Combustion',
     'description': 'Ignite your inner fire - all fire spells are guaranteed critical hits.\n\n'
                    'MECHANICS:\n'
                    '- 100% fire spell critical chance\n'
                    '- +8 damage bonus\n'
                    '- 24 second duration\n'
                    '- 3 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Mage class\n'
                    '- Level 56\n',
     'syntax': "cast 'combustion'",
     'level': 56,
     'mana': 80,
     'cooldown': 180,
 },
 'meteor_storm': {
     'category': 'spell',
     'classes': ['mage'],
     'title': 'Meteor Storm',
     'description': 'CAPSTONE ABILITY: Call down a cataclysmic meteor storm from the heavens.\n\n'
                    'MECHANICS:\n'
                    '- MASSIVE AoE damage to all enemies\n'
                    '- Stuns all targets\n'
                    '- Leaves burning ground (DoT)\n'
                    '- 10 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Mage class\n'
                    '- Level 60\n',
     'syntax': "cast 'meteor storm'",
     'level': 60,
     'mana': 200,
     'cooldown': 600,
 },

 # ----- CLERIC LEVEL 31-60 -----
 'prayer_of_mending': {
     'category': 'spell',
     'classes': ['cleric'],
     'title': 'Prayer of Mending',
     'description': 'Place a prayer on a target that heals them and bounces to other injured allies.\n\n'
                    'MECHANICS:\n'
                    '- Heals target\n'
                    '- Bounces to 3 other injured allies\n'
                    '- 15 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Cleric class\n'
                    '- Level 32\n',
     'syntax': "cast 'prayer of mending' <target>",
     'level': 32,
     'mana': 60,
     'cooldown': 15,
 },
 'spirit_link': {
     'category': 'spell',
     'classes': ['cleric'],
     'title': 'Spirit Link',
     'description': 'Link the spirits of your party, sharing damage equally among all members.\n\n'
                    'MECHANICS:\n'
                    '- All damage taken is split among party\n'
                    '- 30 second duration\n'
                    '- 2 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Cleric class\n'
                    '- Level 38\n',
     'syntax': "cast 'spirit link'",
     'level': 38,
     'mana': 100,
     'cooldown': 120,
 },
 'mass_dispel': {
     'category': 'spell',
     'classes': ['cleric'],
     'title': 'Mass Dispel',
     'description': 'Unleash a wave of purifying energy that removes all debuffs from allies and buffs from enemies.\n\n'
                    'MECHANICS:\n'
                    '- Removes all debuffs from allies\n'
                    '- Removes all buffs from enemies\n'
                    '- 1 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Cleric class\n'
                    '- Level 44\n',
     'syntax': "cast 'mass dispel'",
     'level': 44,
     'mana': 80,
     'cooldown': 60,
 },
 'lightwell': {
     'category': 'spell',
     'classes': ['cleric'],
     'title': 'Lightwell',
     'description': 'Summon a radiant lightwell that heals all allies in the room over time.\n\n'
                    'MECHANICS:\n'
                    '- Heals all allies each tick\n'
                    '- Lasts 60 seconds\n'
                    '- 3 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Cleric class\n'
                    '- Level 50\n',
     'syntax': "cast 'lightwell'",
     'level': 50,
     'mana': 100,
     'cooldown': 180,
 },
 'serenity': {
     'category': 'spell',
     'classes': ['cleric'],
     'title': 'Serenity',
     'description': 'Channel pure divine serenity, fully restoring a target\'s health.\n\n'
                    'MECHANICS:\n'
                    '- Fully heals one target\n'
                    '- 3 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Cleric class\n'
                    '- Level 56\n',
     'syntax': "cast 'serenity' <target>",
     'level': 56,
     'mana': 150,
     'cooldown': 180,
 },
 'divine_intervention': {
     'category': 'spell',
     'classes': ['cleric'],
     'title': 'Divine Intervention',
     'description': 'CAPSTONE ABILITY: Invoke direct divine intervention from the gods.\n\n'
                    'MECHANICS:\n'
                    '- Fully heals entire party\n'
                    '- Resurrects any dead party members\n'
                    '- Grants temporary immunity\n'
                    '- 10 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Cleric class\n'
                    '- Level 60\n',
     'syntax': "cast 'divine intervention'",
     'level': 60,
     'mana': 300,
     'cooldown': 600,
 },

 # ----- THIEF LEVEL 31-60 -----
 'nerve_strike': {
     'category': 'skill',
     'classes': ['thief'],
     'title': 'Nerve Strike',
     'description': 'Strike a target\'s nerve cluster, paralyzing them.\n\n'
                    'MECHANICS:\n'
                    '- Paralyzes target for 6 seconds\n'
                    '- 30 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Thief class\n'
                    '- Level 32\n',
     'syntax': 'nerve_strike [target]',
     'level': 32,
     'cooldown': 30,
 },
 'garrote': {
     'category': 'skill',
     'classes': ['thief'],
     'title': 'Garrote',
     'description': 'Strangle a target from stealth, silencing them and causing bleed damage.\n\n'
                    'MECHANICS:\n'
                    '- Must be used from stealth\n'
                    '- Silences target for 10 seconds\n'
                    '- Applies strong bleed DoT\n'
                    '- 20 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Thief class\n'
                    '- Level 44\n',
     'syntax': 'garrote <target>',
     'level': 44,
     'cooldown': 20,
 },
 'evasion_master': {
     'category': 'skill',
     'classes': ['thief'],
     'title': 'Evasion',
     'description': 'Enter a state of perfect evasion - 100% dodge chance for 10 seconds.\n\n'
                    'MECHANICS:\n'
                    '- All physical attacks miss\n'
                    '- 10 second duration\n'
                    '- 3 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Thief class\n'
                    '- Level 50\n',
     'syntax': 'evasion',
     'level': 50,
     'cooldown': 180,
 },
 'marked_for_death_thief': {
     'category': 'skill',
     'classes': ['thief'],
     'title': 'Marked for Death',
     'description': 'Mark a target for death - all your attacks deal 50% bonus damage.\n\n'
                    'MECHANICS:\n'
                    '- +50% damage to marked target\n'
                    '- Lasts 20 seconds\n'
                    '- 1 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Thief class\n'
                    '- Level 56\n',
     'syntax': 'marked_for_death <target>',
     'level': 56,
     'cooldown': 60,
 },
 'perfect_crime': {
     'category': 'skill',
     'classes': ['thief'],
     'title': 'Perfect Crime',
     'description': 'CAPSTONE ABILITY: 30 seconds of permanent stealth with guaranteed critical hits.\n\n'
                    'MECHANICS:\n'
                    '- Cannot be detected\n'
                    '- All attacks are critical hits\n'
                    '- 30 second duration\n'
                    '- 10 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Thief class\n'
                    '- Level 60\n',
     'syntax': 'perfect_crime',
     'level': 60,
     'cooldown': 600,
 },

 # ----- RANGER LEVEL 31-60 -----
 'volley_master': {
     'category': 'skill',
     'classes': ['ranger'],
     'title': 'Volley',
     'description': 'Rain arrows on all enemies in the room.\n\n'
                    'MECHANICS:\n'
                    '- AoE damage to all enemies\n'
                    '- 20 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Ranger class\n'
                    '- Level 32\n',
     'syntax': 'volley',
     'level': 32,
     'cooldown': 20,
 },
 'camouflage_master': {
     'category': 'skill',
     'classes': ['ranger'],
     'title': 'Camouflage',
     'description': 'Enter advanced camouflage - much harder to detect than regular hide.\n\n'
                    'MECHANICS:\n'
                    '- Superior stealth\n'
                    '- +30 to stealth checks\n'
                    '- 40 second duration\n'
                    '- 30 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Ranger class\n'
                    '- Level 38\n',
     'syntax': 'camouflage',
     'level': 38,
     'cooldown': 30,
 },
 'serpent_sting': {
     'category': 'skill',
     'classes': ['ranger'],
     'title': 'Serpent Sting',
     'description': 'Apply a strong poison DoT to your target.\n\n'
                    'MECHANICS:\n'
                    '- Initial damage + poison DoT\n'
                    '- DoT lasts 20 seconds\n'
                    '- 15 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Ranger class\n'
                    '- Level 44\n',
     'syntax': 'serpent_sting <target>',
     'level': 44,
     'cooldown': 15,
 },
 'rapid_fire': {
     'category': 'skill',
     'classes': ['ranger'],
     'title': 'Rapid Fire',
     'description': 'Fire a rapid barrage of 5-7 arrows at your target.\n\n'
                    'MECHANICS:\n'
                    '- Multiple hits in quick succession\n'
                    '- 1 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Ranger class\n'
                    '- Level 50\n',
     'syntax': 'rapid_fire [target]',
     'level': 50,
     'cooldown': 60,
 },
 'kill_command': {
     'category': 'skill',
     'classes': ['ranger'],
     'title': 'Kill Command',
     'description': 'Command your pet to execute a wounded target.\n\n'
                    'MECHANICS:\n'
                    '- High damage attack\n'
                    '- DOUBLE damage if target below 35% HP\n'
                    '- 45 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Ranger class\n'
                    '- Level 56\n'
                    '- Must have a pet\n',
     'syntax': 'kill_command [target]',
     'level': 56,
     'cooldown': 45,
 },
 'alpha_pack': {
     'category': 'skill',
     'classes': ['ranger'],
     'title': 'Alpha Pack',
     'description': 'CAPSTONE ABILITY: Summon ALL pet types simultaneously in a frenzy.\n\n'
                    'MECHANICS:\n'
                    '- Summons wolf, bear, hawk, cat, and boar\n'
                    '- All pets are in permanent frenzy\n'
                    '- Lasts 30 seconds\n'
                    '- 10 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Ranger class\n'
                    '- Level 60\n',
     'syntax': 'alpha_pack',
     'level': 60,
     'cooldown': 600,
 },

 # ----- PALADIN LEVEL 31-60 -----
 'hand_of_freedom': {
     'category': 'spell',
     'classes': ['paladin'],
     'title': 'Hand of Freedom',
     'description': 'Grant a target freedom from all movement-impairing effects.\n\n'
                    'MECHANICS:\n'
                    '- Removes snares, roots, slows\n'
                    '- Immunity for 16 seconds\n'
                    '- 30 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Paladin class\n'
                    '- Level 32\n',
     'syntax': "cast 'hand of freedom' <target>",
     'level': 32,
     'mana': 40,
     'cooldown': 30,
 },
 'consecration': {
     'category': 'spell',
     'classes': ['paladin'],
     'title': 'Consecration',
     'description': 'Consecrate the ground with holy fire, damaging enemies standing in it.\n\n'
                    'MECHANICS:\n'
                    '- Damages all enemies in room each tick\n'
                    '- Lasts 20 seconds\n'
                    '- 20 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Paladin class\n'
                    '- Level 38\n',
     'syntax': "cast 'consecration'",
     'level': 38,
     'mana': 60,
     'cooldown': 20,
 },
 'hammer_of_justice': {
     'category': 'spell',
     'classes': ['paladin'],
     'title': 'Hammer of Justice',
     'description': 'Hurl a hammer of holy justice that stuns your target.\n\n'
                    'MECHANICS:\n'
                    '- Ranged stun attack\n'
                    '- Stuns for 8 seconds\n'
                    '- 45 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Paladin class\n'
                    '- Level 44\n',
     'syntax': "cast 'hammer of justice' <target>",
     'level': 44,
     'mana': 50,
     'cooldown': 45,
 },
 'avenging_wrath_master': {
     'category': 'spell',
     'classes': ['paladin'],
     'title': 'Avenging Wrath',
     'description': 'Wings of golden light burst from your back as divine wrath fills you.\n\n'
                    'MECHANICS:\n'
                    '- +12 damage, +8 hit\n'
                    '- +30% healing power\n'
                    '- Haste effect\n'
                    '- 40 second duration\n'
                    '- 3 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Paladin class\n'
                    '- Level 50\n',
     'syntax': "cast 'avenging wrath'",
     'level': 50,
     'mana': 120,
     'cooldown': 180,
 },
 'divine_shield_master': {
     'category': 'spell',
     'classes': ['paladin'],
     'title': 'Divine Shield',
     'description': 'Surround yourself with an impenetrable divine shield - complete immunity.\n\n'
                    'MECHANICS:\n'
                    '- IMMUNE to all damage\n'
                    '- 16 second duration\n'
                    '- 5 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Paladin class\n'
                    '- Level 56\n',
     'syntax': "cast 'divine shield'",
     'level': 56,
     'mana': 80,
     'cooldown': 300,
 },
 'crusaders_judgment': {
     'category': 'spell',
     'classes': ['paladin'],
     'title': "Crusader's Judgment",
     'description': 'CAPSTONE ABILITY: The ultimate judgment of the Light.\n\n'
                    'MECHANICS:\n'
                    '- MASSIVE holy damage to target\n'
                    '- Grants party temporary invulnerability\n'
                    '- Resurrects dead party members\n'
                    '- 10 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Paladin class\n'
                    '- Level 60\n',
     'syntax': "cast 'crusaders judgment' <target>",
     'level': 60,
     'mana': 250,
     'cooldown': 600,
 },

 # ----- NECROMANCER LEVEL 31-60 -----
 'death_coil': {
     'category': 'spell',
     'classes': ['necromancer'],
     'title': 'Death Coil',
     'description': 'Hurl a coil of death energy. Damages enemies OR heals your undead minions.\n\n'
                    'MECHANICS:\n'
                    '- Damages living targets\n'
                    '- Heals undead pets\n'
                    '- 12 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Necromancer class\n'
                    '- Level 32\n',
     'syntax': "cast 'death coil' <target>",
     'level': 32,
     'mana': 45,
     'cooldown': 12,
 },
 'corpse_shield': {
     'category': 'spell',
     'classes': ['necromancer'],
     'title': 'Corpse Shield',
     'description': 'Your undead minion forms a protective barrier, absorbing damage for you.\n\n'
                    'MECHANICS:\n'
                    '- 50% of damage redirected to minion\n'
                    '- Lasts 30 seconds\n'
                    '- 1 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Necromancer class\n'
                    '- Level 38\n',
     'syntax': "cast 'corpse shield'",
     'level': 38,
     'mana': 60,
     'cooldown': 60,
 },
 'plague_strike': {
     'category': 'spell',
     'classes': ['necromancer'],
     'title': 'Plague Strike',
     'description': 'Strike with virulent plague that spreads to nearby enemies.\n\n'
                    'MECHANICS:\n'
                    '- Infects target with plague\n'
                    '- Spreads to nearby enemies\n'
                    '- 20 second duration\n'
                    '- 20 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Necromancer class\n'
                    '- Level 44\n',
     'syntax': "cast 'plague strike' <target>",
     'level': 44,
     'mana': 55,
     'cooldown': 20,
 },
 'summon_gargoyle': {
     'category': 'spell',
     'classes': ['necromancer'],
     'title': 'Summon Gargoyle',
     'description': 'Summon a fearsome gargoyle from the shadows to fight for you.\n\n'
                    'MECHANICS:\n'
                    '- Summons a powerful flying pet\n'
                    '- Lasts 60 seconds\n'
                    '- 3 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Necromancer class\n'
                    '- Level 50\n',
     'syntax': "cast 'summon gargoyle'",
     'level': 50,
     'mana': 100,
     'cooldown': 180,
 },
 'soul_harvest': {
     'category': 'spell',
     'classes': ['necromancer'],
     'title': 'Soul Harvest',
     'description': 'Harvest the essence of fallen souls, gaining massive power.\n\n'
                    'MECHANICS:\n'
                    '- Gains soul fragments from nearby corpses\n'
                    '- Empowers necromancer abilities\n'
                    '- 2 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Necromancer class\n'
                    '- Level 56\n',
     'syntax': "cast 'soul harvest'",
     'level': 56,
     'mana': 80,
     'cooldown': 120,
 },
 'apocalypse_necro': {
     'category': 'spell',
     'classes': ['necromancer'],
     'title': 'Apocalypse',
     'description': 'CAPSTONE ABILITY: Raise EVERY corpse in the zone as your army.\n\n'
                    'MECHANICS:\n'
                    '- Raises all corpses in the zone\n'
                    '- Creates massive undead army\n'
                    '- 10 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Necromancer class\n'
                    '- Level 60\n',
     'syntax': "cast 'apocalypse'",
     'level': 60,
     'mana': 250,
     'cooldown': 600,
 },

 # ----- BARD LEVEL 31-60 -----
 'hymn_of_hope': {
     'category': 'spell',
     'classes': ['bard'],
     'title': 'Hymn of Hope',
     'description': 'Sing a hymn of hope that restores mana to your party.\n\n'
                    'MECHANICS:\n'
                    '- +100% mana regen for party\n'
                    '- +50 max mana\n'
                    '- 40 second duration\n'
                    '- 1 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Bard class\n'
                    '- Level 32\n',
     'syntax': "cast 'hymn of hope'",
     'level': 32,
     'mana': 50,
     'cooldown': 60,
 },
 'chord_of_disruption': {
     'category': 'spell',
     'classes': ['bard'],
     'title': 'Chord of Disruption',
     'description': 'Strike a discordant chord that silences all enemies in the room.\n\n'
                    'MECHANICS:\n'
                    '- AoE silence\n'
                    '- 8 second duration\n'
                    '- 45 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Bard class\n'
                    '- Level 38\n',
     'syntax': "cast 'chord of disruption'",
     'level': 38,
     'mana': 70,
     'cooldown': 45,
 },
 'epic_tale': {
     'category': 'spell',
     'classes': ['bard'],
     'title': 'Epic Tale',
     'description': 'Weave an epic tale that buffs ALL stats for your party.\n\n'
                    'MECHANICS:\n'
                    '- +3 to ALL stats for party\n'
                    '- 60 second duration\n'
                    '- 2 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Bard class\n'
                    '- Level 44\n',
     'syntax': "cast 'epic tale'",
     'level': 44,
     'mana': 100,
     'cooldown': 120,
 },
 'siren_song': {
     'category': 'spell',
     'classes': ['bard'],
     'title': 'Siren Song',
     'description': 'Sing an irresistible siren song that charms all enemies.\n\n'
                    'MECHANICS:\n'
                    '- Mass charm effect\n'
                    '- 16 second duration\n'
                    '- 90 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Bard class\n'
                    '- Level 50\n',
     'syntax': "cast 'siren song'",
     'level': 50,
     'mana': 80,
     'cooldown': 90,
 },
 'requiem': {
     'category': 'spell',
     'classes': ['bard'],
     'title': 'Requiem',
     'description': 'Begin a haunting requiem that drains the life of enemies over time.\n\n'
                    'MECHANICS:\n'
                    '- AoE DoT to all enemies\n'
                    '- 30 second duration\n'
                    '- 2 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Bard class\n'
                    '- Level 56\n',
     'syntax': "cast 'requiem'",
     'level': 56,
     'mana': 100,
     'cooldown': 120,
 },
 'magnum_opus': {
     'category': 'spell',
     'classes': ['bard'],
     'title': 'Magnum Opus',
     'description': 'CAPSTONE ABILITY: Perform your ultimate masterpiece.\n\n'
                    'MECHANICS:\n'
                    '- All songs active simultaneously\n'
                    '- +5 all stats\n'
                    '- +10 hit/damage\n'
                    '- Haste + 20% damage reduction\n'
                    '- 60 second duration\n'
                    '- 10 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Bard class\n'
                    '- Level 60\n',
     'syntax': "cast 'magnum opus'",
     'level': 60,
     'mana': 200,
     'cooldown': 600,
 },

 # ----- ASSASSIN LEVEL 31-60 -----
 'shadowstrike': {
     'category': 'skill',
     'classes': ['assassin'],
     'title': 'Shadowstrike',
     'description': 'Teleport through shadows behind your target and backstab them.\n\n'
                    'MECHANICS:\n'
                    '- Instant teleport to target\n'
                    '- Backstab damage\n'
                    '- 20 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Assassin class\n'
                    '- Level 32\n',
     'syntax': 'shadowstrike <target>',
     'level': 32,
     'cooldown': 20,
 },
 'fan_of_knives': {
     'category': 'skill',
     'classes': ['assassin'],
     'title': 'Fan of Knives',
     'description': 'Throw poisoned knives at all enemies in the room.\n\n'
                    'MECHANICS:\n'
                    '- AoE damage + poison\n'
                    '- 15 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Assassin class\n'
                    '- Level 38\n',
     'syntax': 'fan_of_knives',
     'level': 38,
     'cooldown': 15,
 },
 'rupture': {
     'category': 'skill',
     'classes': ['assassin'],
     'title': 'Rupture',
     'description': 'Cause massive bleeding with a vicious strike.\n\n'
                    'MECHANICS:\n'
                    '- High damage + strong bleed DoT\n'
                    '- Bleed lasts 16 seconds\n'
                    '- 20 second cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Assassin class\n'
                    '- Level 44\n',
     'syntax': 'rupture [target]',
     'level': 44,
     'cooldown': 20,
 },
 'shadow_blades_master': {
     'category': 'skill',
     'classes': ['assassin'],
     'title': 'Shadow Blades',
     'description': 'Conjure shadow weapons that deal bonus damage.\n\n'
                    'MECHANICS:\n'
                    '- +20 damage for 24 seconds\n'
                    '- Haste effect\n'
                    '- 2 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Assassin class\n'
                    '- Level 50\n',
     'syntax': 'shadow_blades',
     'level': 50,
     'cooldown': 120,
 },
 'vendetta_assassin': {
     'category': 'skill',
     'classes': ['assassin'],
     'title': 'Vendetta',
     'description': 'Swear a vendetta against a target - ALL damage to them is doubled.\n\n'
                    'MECHANICS:\n'
                    '- 100% bonus damage to target\n'
                    '- 20 second duration\n'
                    '- 2 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Assassin class\n'
                    '- Level 56\n',
     'syntax': 'vendetta <target>',
     'level': 56,
     'cooldown': 120,
 },
 'death_mark': {
     'category': 'skill',
     'classes': ['assassin'],
     'title': 'Death Mark',
     'description': 'CAPSTONE ABILITY: Execute a boss at <25% HP instantly.\n\n'
                    'MECHANICS:\n'
                    '- INSTANT KILL on target below 25% HP\n'
                    '- Works on bosses\n'
                    '- 10 minute cooldown\n\n'
                    'REQUIREMENTS:\n'
                    '- Assassin class\n'
                    '- Level 60\n',
     'syntax': 'death_mark <target>',
     'level': 60,
     'cooldown': 600,
 },
}

# Category index for help listing
HELP_CATEGORIES = {'class': ['assassin', 'bard', 'cleric', 'mage', 'necromancer', 'paladin', 'ranger', 'thief', 'warrior'],
 'command': ['account',
             'achievements',
             'adrenaline_rush',
             'advance',
             'ai',
             'aimed_shot',
             'aistatus',
             'alias',
             'animate',
             'answer',
             'apologize',
             'ascii',
             'ask',
             'assist',
             'at',
             'attack',
             'auction',
             'aura',
             'autoattack',
             'autocombat',
             'autoexit',
             'autogold',
             'autoloot',
             'autorecall',
             'avatar_of_war',
             'backup',
             'balance',
             'bestial_wrath',
             'bind',
             'black_arrow',
             'blade_dance',
             'bladestorm',
             'blush',
             'bow',
             'brief',
             'bug',
             'buy',
             'cackle',
             'cast',
             'changelog',
             'chat',
             'chathistory',
             'cheer',
             'clear',
             'cloak_of_shadows',
             'close',
             'cold_blood',
             'collections',
             'color',
             'combat',
             'combo',
             'comfort',
             'commands',
             'compact',
             'companion',
             'companions',
             'compare',
             'consider',
             'cover',
             'craft',
             'cringe',
             'crippling_poison',
             'crusader_strike',
             'cry',
             'daily',
             'dance',
             'dc',
             'deadly_poison',
             'death_from_above',
             'deposit',
             'diagnose',
             'dismiss',
             'dismount',
             'display',
             'divine_storm',
             'divinefavor',
             'donate',
             'down',
             'drink',
             'drink_alt',
             'drop',
             'dungeon',
             'east',
             'eat',
             'echo',
             'emote',
             'encore',
             'enter',
             'equipment',
             'eviscerate',
             'examine',
             'execute',
             'exits',
             'explosive_trap',
             'faction',
             'fill',
             'find',
             'flee',
             'follow',
             'force',
             'freeze',
             'gather',
             'gecho',
             'get',
             'giggle',
             'give',
             'glare',
             'gossip',
             'goto',
             'grats',
             'greet',
             'grin',
             'group',
             'grumble',
             'gtell',
             'help',
             'hint',
             'hire',
             'holler',
             'holylight',
             'holysmite',
             'house',
             'hug',
             'hunters_mark',
             'idea',
             'ignorepain',
             'imbue',
             'immlist',
             'info',
             'interrupt',
             'inventory',
             'invis',
             'journal',
             'judgment',
             'junk',
             'kidneyshot',
             'kill',
             'killing_spree',
             'knock',
             'label',
             'laugh',
             'layhands',
             'leaderboard',
             'leave',
             'levels',
             'list',
             'load',
             'lock',
             'look',
             'loot',
             'map',
             'mapurl',
             'mark',
             'marked_for_death',
             'marked_shot',
             'medit',
             'minimap',
             'minions',
             'mlist',
             'mload',
             'mock',
             'mortal_strike',
             'motd',
             'mount',
             'mounts',
             'move',
             'mute',
             'mutilate',
             'newgameplus',
             'news',
             'nod',
             'nohassle',
             'norepeat',
             'north',
             'noshout',
             'notell',
             'notick',
             'oedit',
             'olist',
             'oload',
             'open',
             'order',
             'overpower',
             'pat',
             'peace',
             'perform',
             'pet',
             'pets',
             'pick',
             'poke',
             'policy',
             'ponder',
             'pour',
             'practice',
             'predators_mark',
             'preparation',
             'prompt',
             'pull',
             'purge',
             'push',
             'put',
             'qsay',
             'quaff',
             'quest',
             'questlog',
             'quit',
             'rage',
             'raise',
             'rampage',
             'rapid_shot',
             'read',
             'recall',
             'recite',
             'redit',
             'relight',
             'remove',
             'rend',
             'rent',
             'report',
             'reputation',
             'rest',
             'restore',
             'retrieve',
             'ritual',
             'rlist',
             'sacred_shield',
             'sacrifice',
             'salute',
             'save',
             'say',
             'score',
             'seal_of_command',
             'search',
             'sell',
             'set',
             'sets',
             'settings',
             'shadow_blade',
             'shadow_blink',
             'shadow_dance',
             'shadowstep',
             'shield_bash',
             'shield_wall',
             'shout',
             'show',
             'shrug',
             'shutdown',
             'sigh',
             'silence_strike',
             'sit',
             'skill',
             'skills',
             'slap',
             'slay',
             'slicedice',
             'slip_away',
             'smile',
             'snicker',
             'snoop',
             'snuff',
             'social',
             'socials',
             'songs',
             'soulstone',
             'south',
             'spells',
             'split',
             'stable',
             'stampede',
             'stance',
             'stand',
             'stat',
             'stop',
             'storage',
             'store',
             'story',
             'sunder_armor',
             'take',
             'talents',
             'talk',
             'target',
             'taste',
             'tell',
             'thank',
             'tick',
             'tickle',
             'time',
             'time_old',
             'title',
             'toggle',
             'transfer',
             'travel',
             'turnundead',
             'typo',
             'unalias',
             'uncover',
             'ungroup',
             'unlabel',
             'unlock',
             'up',
             'updates',
             'value',
             'vanish',
             'vendetta',
             'visible',
             'volley',
             'wake',
             'warcry',
             'wave',
             'waypoints',
             'wear',
             'weather',
             'west',
             'where',
             'who',
             'wield',
             'wimpy',
             'wink',
             'withdraw',
             'wizhelp',
             'wizinvis',
             'worth',
             'wyvern_sting',
             'xp',
             'yawn',
             'zreset'],
 'skill': ['ambush',
           'assassinate',
           'backstab',
           'bash',
           'battleshout',
           'blur',
           'camouflage',
           'circle',
           'cleave',
           'countersong',
           'detect_traps',
           'disarm',
           'dodge',
           'dual_wield',
           'envenom',
           'evasion',
           'fascinate',
           'feint',
           'garrote',
           'hide',
           'holy_smite',
           'intimidate',
           'kick',
           'lore',
           'mark_target',
           'mockery',
           'parry',
           'pick_lock',
           'rescue',
           'scan',
           'scribe',
           'second_attack',
           'shadow_step',
           'shield_block',
           'smite',
           'sneak',
           'steal',
           'tame',
           'third_attack',
           'track',
           'trip',
           'tumble',
           'turn_undead'],
 'spell': ['aegis',
           'animate_dead',
           'armor',
           'barkskin',
           'bless',
           'blindness',
           'blink',
           'burning_hands',
           'call_lightning',
           'chain_lightning',
           'charm_person',
           'chill_touch',
           'color_spray',
           'create_food',
           'create_water',
           'cure_critical',
           'cure_light',
           'cure_serious',
           'death_grip',
           'detect_evil',
           'detect_magic',
           'dispel_evil',
           'displacement',
           'divine_protection',
           'divine_shield',
           'earthquake',
           'enchant_weapon',
           'energy_drain',
           'enervation',
           'entangle',
           'faerie_fire',
           'fear',
           'finger_of_death',
           'fire_shield',
           'fireball',
           'flamestrike',
           'fly',
           'group_heal',
           'harm',
           'haste',
           'heal',
           'heroism',
           'holy_aura',
           'ice_armor',
           'identify',
           'invisibility',
           'lightning_bolt',
           'magic_missile',
           'mana_shield',
           'mass_charm',
           'meteor_swarm',
           'mirror_image',
           'poison',
           'protection_from_evil',
           'protection_from_good',
           'remove_curse',
           'remove_poison',
           'resurrect',
           'righteous_fury',
           'sanctuary',
           'shield',
           'shield_of_faith',
           'sleep',
           'slow',
           'spell_reflection',
           'stoneskin',
           'summon',
           'teleport',
           'vampiric_touch',
           'weaken',
           'word_of_recall']}

def get_help_text(topic: str) -> str:
    """Get formatted help text for a topic."""
    topic = topic.lower().replace(" ", "_")

    if topic in HELP_TOPICS:
        help_data = HELP_TOPICS[topic]
        output = []
        output.append("=" * 70)
        output.append(help_data["title"].center(70))
        output.append("=" * 70)

        if "syntax" in help_data:
            output.append("\nSYNTAX: " + help_data["syntax"])

        if help_data.get("category") == "skill":
            output.append("AVAILABLE TO: " + ", ".join(help_data.get("classes", [])))
        elif help_data.get("category") == "spell":
            output.append("AVAILABLE TO: " + ", ".join(help_data.get("classes", [])))
            output.append("LEVEL: " + str(help_data.get("level", 1)) + " | MANA: " + str(help_data.get("mana", 0)))

        output.append(help_data["description"])
        output.append("=" * 70)
        return "\n".join(output)

    return None

def get_help_index() -> str:
    """Get a categorized index of all help topics."""
    output = []
    output.append("=" * 70)
    output.append("HELP SYSTEM".center(70))
    output.append("=" * 70)
    output.append("\nType 'help <topic>' for detailed information.\n")

    for cat in sorted(HELP_CATEGORIES.keys()):
        output.append(cat.upper() + ":")
        for topic in HELP_CATEGORIES[cat]:
            output.append("  " + topic)
        output.append("")

    return "\n".join(output)