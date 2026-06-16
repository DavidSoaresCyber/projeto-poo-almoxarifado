import json
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database.connection import get_db, SessionLocal
from app.schemas.schemas import IAChatRequest, IAChatResponse
from app.security.auth import get_current_user, decode_token
from app.models.models import Usuario
from app.services.morangia import MorangIAService

router = APIRouter(prefix="/morangia", tags=["MorangIA"])


@router.post("/chat", response_model=IAChatResponse)
def chat(data: IAChatRequest, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    service = MorangIAService(db, user)
    result = service.processar(data.mensagem)
    return IAChatResponse(**result)


@router.get("/sugestoes")
def sugestoes(user: Usuario = Depends(get_current_user)):
    return {"sugestoes": MorangIAService.SUGESTOES_PADRAO}


class ConnectionManager:
    def __init__(self):
        self.active: dict[int, WebSocket] = {}

    async def connect(self, ws: WebSocket, user_id: int):
        await ws.accept()
        self.active[user_id] = ws

    def disconnect(self, user_id: int):
        self.active.pop(user_id, None)

    async def send(self, user_id: int, message: str):
        if user_id in self.active:
            await self.active[user_id].send_text(message)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket, token: str = ""):
    db = SessionLocal()
    try:
        if not token:
            await websocket.close(code=4001)
            return
        payload = decode_token(token.replace("Bearer ", ""))
        user = db.query(Usuario).filter(Usuario.id == int(payload["sub"])).first()
        if not user:
            await websocket.close(code=4001)
            return

        await manager.connect(websocket, user.id)

        while True:
            data = await websocket.receive_text()
            msg_data = json.loads(data)
            service = MorangIAService(db, user)
            result = service.processar(msg_data.get("mensagem", ""))
            await websocket.send_text(json.dumps(result, ensure_ascii=False))
    except WebSocketDisconnect:
        if user:
            manager.disconnect(user.id)
    finally:
        db.close()
