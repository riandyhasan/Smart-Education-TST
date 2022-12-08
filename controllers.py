from sqlalchemy.orm import Session
import models, schemas
import geopy.distance

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
    nearest = []
    while nearest == []:
      for sma in all_sma:
          coord_2 = (sma.latitude, sma.longitude)
          distance = geopy.distance.geodesic(coord_1, coord_2).km
          if(distance <= radius):
            nearest.append(sma)
      if nearest == []:
        radius += 0.5
      if radius > 15:
        return []
    return models.Serializer.serialize_list(nearest)
