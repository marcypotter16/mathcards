

from entities.game_manager.dataclasses import GameAction


class GameManager:
    def __init__(self, local_player_id: str) -> None:
        self.local_player_id = local_player_id
        
        # If playing online, you'd have a reference to your networking client interface
        # self.network_client = network_client

    def request_action(self, action: GameAction):
        """
        Called locally when the player interacts with the UI (e.g., dragging a card from hand to board).
        """
        # 1. (Optional Client-Side Validation) Check if the move is legal locally first for responsiveness
        if not self.validate_action(action):
            print("Illegal action attempted locally.")
            return

        # 2. In multiplayer, send to server instead of executing immediately (or use optimistic prediction)
        # self.network_client.send(action.to_dict())
        
        # For single-player or testing, execute directly:
        self.execute_action(action)

    def execute_action(self, action: GameAction):
        """
        The core brain. Executes the action on the game state regardless of 
        whether it came from the local player or the opponent over the network.
        """
        match action.action_type:
            case ActionType.PLAY_CARD_FROM_HAND:
                card_id = action.payload.get("card_id")
                target_board_index = action.payload.get("target_index")
                
                # Logic: Find card in hand, remove it, add it to the board manager
                self._handle_play_card(action.player_id, card_id, target_board_index)

            case ActionType.ATTACK_TARGET:
                # Handle attack logic between entities
                pass

            case ActionType.END_TURN:
                # Handle turn swapping logic
                pass

            case _:
                print(f"Unknown action type: {action.action_type}")

    def validate_action(self, action: GameAction) -> bool:
        """Basic rule-checking before sending/executing."""
        # e.g., Is it actually this player's turn? Do they have enough mana?
        return True

    def _handle_play_card(self, player_id: str, card_id: int, target_index: int):
        # Implementation of moving a card from hand to board
        # If player_id == self.local_player_id, manipulate your local Hand/Board managers
        # If it's the opponent, manipulate the opponent's visual representation on your screen
        pass