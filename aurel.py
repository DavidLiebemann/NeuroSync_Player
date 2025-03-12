# 1. Connect to ChatGPT Realtime API
# 2. Setup ChatGPT Realtime Agent to act as Marc Aurel
# 3. Record Microphone Input
# 4. Send Microphone Input to ChatGPT Realtime API
# 5. Receive Realtime Answer
# 6. Stream Realtime Answer to NeuroSync API
# 7. Receive NeuroSync API BlendShapes
# 8. Sync BlendShapes with Audio data
# 9. Send BlendShapes and Audio data to Unreal

from dotenv import load_dotenv
import llm_to_face 

load_dotenv()
llm_to_face.main()