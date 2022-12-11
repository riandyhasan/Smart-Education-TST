from pydantic import BaseModel
from models import Akreditasi
from typing import Optional

# DB MODEL
class SMABase(BaseModel):
  npsn: int
  nama_sekolah: str
  alamat: str
  kelurahan: str
  kecamatan: str
  jumlah_siswa: int
  jumlah_guru: int
  kepala_sekolah: str
  telp_sekolah: str
  akreditasi: Akreditasi
  latitude: float
  longitude: float

class UserBase(BaseModel):
  username: str

class CreateSMA(SMABase):
  pass

class CreateUser(UserBase):
  nama: str
  email: str
  password: str

class UpdateSMA(SMABase):
  pass

class UpdateUser(CreateUser):
  pass

class LoginUser(UserBase):
  password: str

class SMA(SMABase):
  pass

  class Config:
    orm_mode = True

class User(UserBase):
  id: int
  nama: str
  email: str
  terverifikasi: bool
  
  class Config:
    orm_mode = True

# QUERY
class QuerySMA(BaseModel):
  npsn: Optional[int]
  kec: Optional[str]
  kel: Optional[str]

class Coordinate(BaseModel):
  lat: float
  lon: float

class UserOTP(BaseModel):
  username: str
  otp: int

class UserVerification(BaseModel):
  user_id: int