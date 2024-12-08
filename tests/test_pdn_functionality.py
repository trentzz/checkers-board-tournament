import pytest

from checkers_bot_tournament.board import Board
from checkers_bot_tournament.board_start_builder import DefaultBSB
from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.game import Game
from checkers_bot_tournament.move import Move


@pytest.fixture
def temp_pdn_file(tmp_path):
    """Creates a temporary PDN file and returns its path."""
    file_path = tmp_path / "test_game.pdn"
    return file_path


@pytest.fixture
def sample_pdn():
    """Returns a sample PDN string for testing."""
    return "22-17 11-15 24-20 15-19 23x16 12x19 27-24 9-13 24x15 13x22"


def test_import_pdn_from_string(temp_pdn_file, sample_pdn):
    """Test that a PDN file is correctly imported into the board."""
    # Write the PDN to a file
    temp_pdn_file.write_text(sample_pdn)

    # Create a board and import the PDN
    game = Game(Bot(0), Bot(0), Board(DefaultBSB()), 0, 0, False, temp_pdn_file)

    # Expected move list (calculated manually)
    expected_moves = [
        Move((5, 2), (4, 1), None),  # 22-17
        Move((2, 5), (3, 4), None),  # 11-15
        Move((5, 6), (4, 7), None),  # 24-20
        Move((3, 4), (4, 5), None),  # 15-19
        Move((5, 4), (3, 6), (4, 5)),  # 23x16 (jump move)
        Move((2, 7), (4, 5), (3, 6)),  # 12x19 (jump move)
        Move((6, 5), (5, 6), None),  # 27-24
        Move((2, 1), (3, 0), None),  # 9-13
        Move((5, 6), (3, 4), (4, 5)),  # 24x15 (jump move)
        Move((3, 0), (5, 2), (4, 1)),  # 13x22 (jump move)
    ]

    print(game.board.move_history)

    assert len(game.board.move_history) == len(expected_moves)

    for move, expected in zip(game.board.move_history, expected_moves):
        assert move.start == expected.start
        assert move.end == expected.end
        assert move.removed == expected.removed


def test_export_pdn(temp_pdn_file):
    """Test that the board's move history is correctly exported to a PDN file."""

    game = Game(Bot(0), Bot(0), Board(DefaultBSB()), 0, 0, False, None)
    moves = [
        Move((5, 2), (4, 1), None),  # 22-17
        Move((2, 5), (3, 4), None),  # 11-15
        Move((5, 6), (4, 7), None),  # 24-20
        Move((3, 4), (4, 5), None),  # 15-19
        Move((5, 4), (3, 6), (4, 5)),  # 23x16 (jump move)
        Move((2, 7), (4, 5), (3, 6)),  # 12x19 (jump move)
        Move((6, 5), (5, 6), None),  # 27-24
        Move((2, 1), (3, 0), None),  # 9-13
        Move((5, 6), (3, 4), (4, 5)),  # 24x15 (jump move)
        Move((3, 0), (5, 2), (4, 1)),  # 13x22 (jump move)
    ]

    for move in moves:
        game.board.move_piece(move)

    # Export the moves to a file
    game.export_pdn(temp_pdn_file)

    # Read the PDN file
    exported_pdn = temp_pdn_file.read_text().strip()

    expected_pdn = "22-17 11-15 24-20 15-19 23x16 12x19 27-24 9-13 24x15 13x22"
    assert exported_pdn == expected_pdn


def test_import_export_consistency(temp_pdn_file, sample_pdn):
    """Test that importing a PDN file and exporting it again produces the same file."""
    # Write the initial PDN to the file
    temp_pdn_file.write_text(sample_pdn)

    # Create a board, import the PDN, and export it to a new file
    game = Game(Bot(0), Bot(0), Board(DefaultBSB()), 0, 0, False, None)
    game.import_pdn(temp_pdn_file)

    # Export to a new PDN file
    export_file_path = temp_pdn_file.with_name("exported_game.pdn")
    game.export_pdn(export_file_path)

    exported_pdn = export_file_path.read_text().strip()

    assert exported_pdn == sample_pdn
