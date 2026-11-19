"""Re-exports for all game logic utilities."""

# Board analysis functions
from .board_analysis import (
    determine_pieces_that_have_moved, 
    get_piece_value, 
    get_move_counts,
    evaluate_current_position,
    get_neutral_monster_slain_positions
)

# Game state functions  
from .game_state import (
    clear_game, 
    increment_turn_count,
    reset_turn_count,
    manage_game_state,
    perform_game_state_update,
    clean_possible_moves_and_possible_captures,
    prevent_client_side_updates_to_graveyard,
    record_moved_pieces_this_turn
)

# Validation functions
from .validation import (
    INVALID_GAME_STATE_ERROR_MESSAGE,
    INVALID_CPU_DIFFICULTY_ERROR_MESSAGE,
    check_to_see_if_more_than_one_piece_has_moved,
    invalidate_game_if_wrong_side_moves,
    invalidate_game_if_more_than_one_side_moved,
    invalidate_game_if_stunned_piece_moves,
    invalidate_game_if_monster_has_moved,
    invalidate_game_if_too_much_gold_is_spent,
    invalidate_game_when_unexplained_pieces_are_in_captured_pieces_array,
    invalidate_game_if_no_marked_for_death_pieces_have_been_selected,
    check_for_disappearing_pieces,
    check_if_pawn_exchange_is_required,
    check_if_pawn_exchange_is_possibly_being_carried_out,
    should_turn_count_be_incremented_for_pawn_exchange,
    get_gold_spent,
    is_invalid_king_capture
)

# Piece mechanics functions
from .piece_mechanics import (
    apply_bishop_energize_stacks_and_bishop_debuffs,
    apply_queen_stun,
    facilitate_adjacent_capture,
    enable_adjacent_bishop_captures,
    handle_pieces_with_full_bishop_debuff_stacks,
    clean_bishop_special_captures
)

# Game scoring functions  
from .game_scoring import (
    get_average_piece_value_for_each_side,
    update_gold_count,
    update_capture_point_advantage,
    reassign_pawn_buffs
)

# Queen mechanics functions
from .queen_mechanics import (
    reset_queen_turn_on_kill_or_assist,
    set_queen_as_position_in_play,
    verify_queen_reset_turn_is_valid
)

# Movement and position functions
from .moves_and_positions import (
    determine_possible_moves,
    was_a_new_position_in_play_selected,
    does_position_in_play_match_turn
)

# Castle mechanics functions
from .castle_mechanics import update_castle_log

# Monster functions
from .monsters import (
    spawn_neutral_monsters, 
    MONSTER_INFO,
    carry_out_neutral_monster_attacks,
    damage_neutral_monsters,
    heal_neutral_monsters,
    is_neutral_monster_spawned,
    is_neutral_monster_killed,
    handle_neutral_monster_buffs
)

# Check and checkmate functions
from .check_checkmate import (
    get_unsafe_positions_for_kings,
    manage_check_status,
    end_game_on_checkmate,
    can_king_move,
    can_other_pieces_prevent_check,
    trim_king_moves,
    trim_moves,
    invalidate_game_if_player_moves_and_is_in_check,
    is_check_due_to_neutral_monster_spawn_this_turn,
    set_next_king_as_position_in_play_if_in_check,
    is_position_in_play_valid_to_save_king
)

# Game ending functions
from .game_ending import (
    handle_draw_conditions,
    tie_game_if_no_moves_are_possible_next_turn,
    are_all_non_king_pieces_stunned
)

# Special items functions
from .special_items import (
    spawn_sword_in_the_stone,
    exhaust_sword_in_the_stone
)

# Stun mechanics functions
from .stun_mechanics import cleanse_stunned_pieces

# Logger
from src.log import logger