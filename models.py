import enum
from sqlalchemy import Float, Column, Integer, String, Enum, Boolean
from database import Base
from sqlalchemy.inspection import inspect

class Serializer(object):
  def serialize(self):
      return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

  @staticmethod
  def serialize_list(l):
      return [m.serialize() for m in l]

class Akreditasi(enum.Enum):
  a = "A"
  b = "B"
  unclassified = "Tidak Terakreditasi"


class SMA(Base):
  __tablename__ = "data_sebaran_sekolah_sma"

  npsn = Column(Integer, primary_key=True)
  nama_sekolah = Column(String)
  alamat = Column(String)
  kelurahan = Column(String)
  kecamatan = Column(String)
  jumlah_siswa = Column(Integer)
  jumlah_guru = Column(Integer)
  kepala_sekolah = Column(String)
  telp_sekolah = Column(String)
  akreditasi = Column(String)
  latitude = Column(Float)
  longitude = Column(Float)

  def serialize(self):
    return Serializer.serialize(self)

class User(Base):
  __tablename__ = "user"

  id = Column(Integer, primary_key=True)
  email = Column(String)
  username = Column(String)
  nama = Column(String)
  password = Column(String)
  terverifikasi = Column(Boolean)
  admin = Column(Boolean)

  def serialize(self):
    d = Serializer.serialize(self)
    del d['password']
    return d
