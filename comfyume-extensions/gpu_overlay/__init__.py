"""
GPU Overlay Extension — ComfyuME

Floating status banner showing GPU inference progress.
Listens for ComfyUI WebSocket events (execution_start, executed,
execution_error) sent by the serverless_proxy extension.

Works in serverless mode where the server-side proxy handles execution
and sends progress events via WebSocket. In non-serverless modes,
queue_redirect has its own HTTP-based progress banner.
"""

NODE_CLASS_MAPPINGS = {}  # No custom nodes, only web extension
WEB_DIRECTORY = "./web"
