import sys
import os
sys.path.append(os.getcwd())

try:
    from services.mock_data import get_mock_customer
    print("✅ services.mock_data imported")
    from api.message import generate_message
    print("✅ api.message imported")
    from actions.message_writer import message_writer_node
    print("✅ actions.message_writer imported")
    from actions.orchestrator import orchestrator_node
    print("✅ actions.orchestrator imported")
    print("ALL IMPORTS OK")
except Exception as e:
    print(f"❌ Import Error: {e}")
