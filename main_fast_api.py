from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

#Definicion de usuarios
class Usuario(BaseModel):
  nombre: str
  email: EmailStr
  preferencias: str

usuarios = []

JSON_PATH = 'users.json'
JSON_PATH2 = 'res.json'

#Creacion de usuarios
@app.post('/api/users')
def crear_usuario(usuario: Usuario):

  try:
      with open(JSON_PATH, "r") as file:
          usuarios = json.load(file)
  except FileNotFoundError:
       usuarios = []

  if any(u['email'] == usuario.email for u in usuarios):
    raise HTTPException(status_code=400, detail="Este email ya existe")
  
  if (len(usuarios) == 0):
    cont = 1
  else:
    cont = usuarios[-1]['id'] + 1

  nuevo_usuario = {
    "id": cont,
    "nombre": usuario.nombre,
    "email": usuario.email,
    "preferencias": usuario.preferencias
  }
  
  usuarios.append(nuevo_usuario)

  with open(JSON_PATH, "w") as file:
        json.dump(usuarios, file, indent=4)

  return {"message": "Usuario creado", "usuario": nuevo_usuario}

#Visualizacion de usuarios
@app.get('/api/users')
def listar_usuarios():

  try:
      with open(JSON_PATH, "r") as file:
          usuarios = json.load(file)
  except FileNotFoundError:
       usuarios = []

  return{"usuarios": usuarios}

#Visualizacion de un usuario especifico
@app.get('/api/users/{id}')
def listar_usuario(id: int):
  
  try:
      with open(JSON_PATH, "r") as file:
          usuarios = json.load(file)
  except FileNotFoundError:
       usuarios = []
  
  try:
     usuario_index = [usuario['id'] for usuario in usuarios].index(id)
  except:
     raise HTTPException(status_code=404, detail="Usuario no existe")

  return {"usuario": usuarios[usuario_index]}

#Actualizacion de un usuario
@app.put('/api/users/{id}')
def actualizar_usuarios(id: int, usuario: Usuario):
  
  try:
      with open(JSON_PATH, "r") as file:
          usuarios = json.load(file)
  except FileNotFoundError:
       usuarios = []
  
  if any(u['email'] == usuario.email for u in usuarios):  #for u in users:
    raise HTTPException(status_code=400, detail="Este email ya existe")
  
  try:
     usuario_index = [usuario['id'] for usuario in usuarios].index(id)
  except:
     raise HTTPException(status_code=404, detail="Usuario no existe")

  usuarios[usuario_index] = {
    "id": id,
    "nombre": usuario.nombre,
    "email": usuario.email,
    "preferencias": usuario.preferencias
  }

  with open(JSON_PATH, "w") as file:
        json.dump(usuarios, file, indent=4)

  return {"message": "Usuario actualizado"}

#Eliminacion de un usuario
@app.delete("/api/users/{id}")
def eliminar_usuario(id: int):
    
  try:
    with open(JSON_PATH, "r") as file:
        usuarios = json.load(file)
  except FileNotFoundError:
     usuarios = []

  try:
     usuario_index = [usuario['id'] for usuario in usuarios].index(id)
  except:
     raise HTTPException(status_code=404, detail="Usuario no existe")

  usuarios.pop(usuario_index)

  with open(JSON_PATH, "w") as file:
        json.dump(usuarios, file, indent=4)

  return {"message": "Usuario eliminado"}

#Consulta a spotify a partir de las preferencias de los usuarios
@app.get("/api/users/{id}/recommendations")
def spotify_info(id: int):
   
  try:
    with open(JSON_PATH, "r") as file:
        usuarios = json.load(file)
  except FileNotFoundError:
     usuarios = []

  try:
     usuario_index = [usuario['id'] for usuario in usuarios].index(id)
  except:
     raise HTTPException(status_code=404, detail="Usuario no existe")
  
  artista_fav = usuarios[usuario_index]['preferencias']

  client_id = os.getenv('CLIENT_ID')
  client_secret = os.getenv('CLIENT_SECRET')

  auth_url = 'https://accounts.spotify.com/api/token'

  data = {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret,
  }

  auth_response = requests.post(auth_url, data=data)

  access_token = auth_response.json().get('access_token')

  base_url = 'https://api.spotify.com/v1/'

  headers = {
    'Authorization': 'Bearer {}'.format(access_token)
  }

  rec = 'browse/new-releases' #url obtiene nuevos lanzamientos
  featured_playlists_url = ''.join([base_url,rec])

  response = requests.get(featured_playlists_url,headers=headers).json()['albums']['items']

  artistas = [res['artists'][0] for res in response]

  nombres_artista = [res2['name'] for res2 in artistas]

  try:
    art_index = [art for art in nombres_artista].index(artista_fav)
  except:
     raise HTTPException(status_code=404, detail="Artista no tiene nuevos lanzamientos")  

  info = {
     'artista': nombres_artista[art_index],
     'album': response[art_index]['name'],
     'fecha': response[art_index]['release_date'],
     'canciones': response[art_index]['total_tracks']
  }

  with open(JSON_PATH2, "w") as file: #se creo archivo JSON para verificar la informacion entregada por la API
        json.dump(response, file, indent=4)
  
  return {"Usuario": usuarios[usuario_index], "Spotify": info}