import datetime


empty_game = {
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
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8
    ]
}
