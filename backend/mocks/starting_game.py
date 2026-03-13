import datetime


starting_game = {
    "turn_count": 0,
    "position_in_play": [None, None],
    "possible_moves": [],
    "possible_captures": [],
    "castle_moves": [],
    "captured_pieces": {"white": [], "black": []},
    "graveyard": [],
    "sword_in_the_stone_position": None,
    "capture_point_advantage": None,
    "black_defeat": False,
    "white_defeat": False,
    "gold_count": {"white": 0, "black": 0},
    "last_updated": datetime.datetime.now(),
    "bishop_special_captures": [],
    "latest_movement": {},
    "queen_reset": False,
    "neutral_attack_log": {},
    "check": {"white": False, "black": False},
    "castle_log": {
        "white": {
            "has_king_moved": False,
            "has_left_rook_moved": False, 
            "has_right_rook_moved": False
        }, 
        "black": {
            "has_king_moved": False,
            "has_left_rook_moved": False, 
            "has_right_rook_moved": False
        }
    },
    "neutral_buff_log": {
        "white": {
            "dragon": {"stacks":0, "turn": 0},
            "board_herald": {"active": False, "turn": 0},
            "baron_nashor": {"active": False, "turn": 0}
        },
        "black": {
            "dragon": {"stacks":0, "turn": 0},
            "board_herald": {"active": False, "turn": 0},
            "baron_nashor": {"active": False, "turn": 0}
        }
    },
    "cpu_id": None,
    "last_checked_by_cpu": None,
    "version": 0,
    "board_state": [
        [
            [{"type": "black_rook"}],
            [{"type": "black_knight"}],
            [{"type": "black_bishop", "energize_stacks": 0}],
            [{"type": "black_queen"}],
            [{"type": "black_king"}],
            [{"type": "black_bishop", "energize_stacks": 0}],
            [{"type": "black_knight"}],
            [{"type": "black_rook"}],
        ],
        [
            [{"type": "black_pawn", "pawn_buff": 0}], 
            [{"type": "black_pawn", "pawn_buff": 0}],
            [{"type": "black_pawn", "pawn_buff": 0}],
            None,
            [{"type": "black_pawn", "pawn_buff": 0}],
            [{"type": "black_pawn", "pawn_buff": 0}],
            [{"type": "black_pawn", "pawn_buff": 0}],
            [{"type": "black_pawn", "pawn_buff": 0}]
        ],
        [
            None,
            None,
            None,
            [{"type": "black_pawn", "pawn_buff": 0}],
            None,
            None,
            None,
            None
        ],
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [[{"type": "white_pawn", "pawn_buff": 0}]] * 8,
        [
            [{"type": "white_rook"}],
            [{"type": "white_knight"}],
            [{"type": "white_bishop", "energize_stacks": 0}],
            [{"type": "white_queen"}],
            [{"type": "white_king"}],
            [{"type": "white_bishop", "energize_stacks": 0}],
            [{"type": "white_knight"}],
            [{"type": "white_rook"}],
        ]
    ]
}
