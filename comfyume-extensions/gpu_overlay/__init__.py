"""
GPU Overlay Extension — ComfyuME

Listens for serverless inference WebSocket events and shows progress
via the status_banner extension. Serverless mode only.

Requires: status_banner extension (provides window.comfyumeStatus).
"""

NODE_CLASS_MAPPINGS = {}
WEB_DIRECTORY = "./web"
