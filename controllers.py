from sqlalchemy.orm import Session
import models, schemas
import geopy.distance
import hashlib

def get_all_sma(db: Session):
  return (models.Serializer).serialize_list(db.query(models.SMA).all())

def get_sma_by_npsn(db: Session, npsn: int):
  q = (db.query(models.SMA).filter(models.SMA.npsn == npsn).first())
  if q:
    return q.serialize()

def get_sma_kel_kec(db: Session, kel: str, kec: str):
  if kel and kec:
    q = (db.query(models.SMA).filter(models.SMA.kelurahan == kel and models.SMA.kecamatan == kec).all())
  elif kel and kec is None:
    q = (db.query(models.SMA).filter(models.SMA.kelurahan == kel).all())
  elif kec and kel is None:
    q = (db.query(models.SMA).filter(models.SMA.kecamatan == kec).all())
  if q:
    return models.Serializer.serialize_list(q)

def get_sma_nearest(db: Session, lat: float, lon: float):
  if lat and lon:
    all_sma = db.query(models.SMA).all()
    coord_1= (lat, lon)
    radius = 1
    temp = []
    for sma in all_sma:
      coord_2 = (sma.latitude, sma.longitude)
      distance = geopy.distance.geodesic(coord_1, coord_2).km
      temp.append({ 'data': sma, 'distance': distance})
    nearest = []
    while nearest == []:
      for _ in temp:
        if(_['distance'] <= radius):
          nearest.append(_['data'])
      if nearest == []:
        radius += 0.5
      if radius > 15:
        return []
    return models.Serializer.serialize_list(nearest)

def add_sma(db: Session, sma: schemas.CreateSMA):
  db_sma = models.SMA(
    npsn=sma.npsn,
    nama_sekolah=sma.nama_sekolah,
    kelurahan=sma.kelurahan,
    kecamatan=sma.kecamatan,
    jumlah_siswa=sma.jumlah_siswa,
    jumlah_guru=sma.jumlah_guru,
    kepala_sekolah=sma.kepala_sekolah,
    telp_sekolah=sma.telp_sekolah,
    akreditasi=sma.akreditasi,
    latitude=sma.latitude,
    longitude=sma.longitude
  )
  db.add(db_sma)
  db.commit()
  db.refresh(db_sma)
  return db_sma

def edit_sma(db: Session, sma: schemas.UpdateSMA):
  db_sma = db.query(models.SMA).filter(models.SMA.npsn == sma.npsn).first()
  if db_sma:
    try:
      db_sma.nama_sekolah=sma.nama_sekolah
      db_sma.kelurahan=sma.kelurahan
      db_sma.kecamatan=sma.kecamatan
      db_sma.jumlah_siswa=sma.jumlah_siswa
      db_sma.jumlah_guru=sma.jumlah_guru
      db_sma.kepala_sekolah=sma.kepala_sekolah
      db_sma.telp_sekolah=sma.telp_sekolah
      db_sma.akreditasi=sma.akreditasi
      db_sma.latitude=sma.latitude
      db_sma.longitude=sma.longitude
      db.add(db_sma)
      db.commit()
      db.refresh(db_sma)
      return db_sma
    except Exception as e:
      return None
  else:
    return None

def delete_sma(db: Session, npsn: int):
  db_sma = db.query(models.SMA).filter(models.SMA.npsn == npsn).first()
  if db_sma:
    db_sma.delete()
    db.commit()
    return True
  return None

def get_user_by_username(db: Session, username: str):
  return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
  return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, id: int):
  return db.query(models.User).filter(models.User.id == id).first()

def add_user(db: Session, user: schemas.CreateUser):
  db_user = models.User(email=user.email, username=user.username, nama=user.nama, password=hash_password(user.password), terverifikasi=False, admin=False)
  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  return db_user

def verify_user(db: Session, user: models.User):
  try: 
    user.terverifikasi = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
  except:
    return None


def hash_password(password):
  sha256 = hashlib.sha256()
  sha256.update(password.encode())
  hashed_password = sha256.hexdigest()
  return hashed_password

def get_penduduk_kelurahan(kelurahan):
  res = {}
  total = 0
  kel = ''
  for _ in kelurahan:
    kel = _['nama_kelurahan']
    if _['usia'] == '15-19':
      total += _['jumlah_penduduk']
  res = { 'kelurahan': kel, 'jumlah_penduduk': total }
  return res

def calculate_keketatan(sma, kel):
  keketatan = 0
  for _ in kel:
    if _['kelurahan'] == sma['kelurahan']:
      keketatan = sma['jumlah_siswa'] / _['jumlah_penduduk']
      break
  return keketatan

def calculate_jarak(point1, point2):
  coord_1 = (point1['lat'], point1['lon'])
  coord_2 = (point2['lat'], point2['lon'])
  return geopy.distance.geodesic(coord_1, coord_2).km

def sort_by_jarak(list):
  return sorted(list, key=lambda d: d['jarak']) 

def sort_by_keketatan(list):
  return sorted(list, key=lambda d: d['keketatan']) 

def sort_by_akreditasi(list):
  akre_a = []
  akre_b = []
  akre_ta = []
  for l in list:
    if l['akreditasi'] == 'A':
      akre_a.append(l)
    elif l['akreditasi'] == 'B':
      akre_b.append(l)
    else:
      akre_ta.append(l)
  return akre_a + akre_b + akre_ta

def sort_recommendations(list):
  return sort_by_akreditasi(sort_by_jarak(sort_by_keketatan(list)))
