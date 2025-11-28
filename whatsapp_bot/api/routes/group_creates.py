"""
This is the API routes for creating various types of WhatsApp groups
like Mavdak, Raf0, Hakhana, etc.
"""


from fastapi import APIRouter, Depends
from fastapi import FastAPI, status
from models import HakhanaRequestModel, MavdakRequestModel, Raf0RequestModel
from mavdak.mavdak import mavdak_full_sequence
from connection import validate_whatsapp_connection
from setup import  get_cursor_dep
from raf0 import raf0

from hakhana import hakhana
from api.dependencies import get_scheduler


group_creates_router = APIRouter(
    prefix="/create_group",
)


# POST endpoint
@group_creates_router.post("/mavdak", status_code=status.HTTP_202_ACCEPTED)
def create_mavdak(payload: MavdakRequestModel, cur = Depends(get_cursor_dep), scheduler = Depends(get_scheduler)):
    
    # Validate WhatsApp connection 
    validate_whatsapp_connection()

    mavdak_full_sequence(payload, scheduler, cur)
    

    return {}


# Minimal API endpoint
@group_creates_router.post("/raf0", status_code=status.HTTP_201_CREATED)
def create_raf0(req: Raf0RequestModel , cur = Depends(get_cursor_dep) , scheduler = Depends(get_scheduler) ):
    
    # Validate WhatsApp connection 
    validate_whatsapp_connection()
    
    raf0(req, scheduler, cur)
    
    return {}
    
# Minimal API endpoint
@group_creates_router.post("/hakhana", status_code=status.HTTP_201_CREATED)
def create_hakhana(req: HakhanaRequestModel, cur = Depends(get_cursor_dep) , scheduler = Depends(get_scheduler) ):
    
    # Validate WhatsApp connection 
    validate_whatsapp_connection()
    
    hakhana(req, scheduler, cur)
    
    return {} 