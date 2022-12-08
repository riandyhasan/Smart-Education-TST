from flask import Flask, jsonify, request, make_response
# from flask_login import LoginManager
import controllers, models, schemas
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import json

app = Flask(__name__)

# login = LoginManager(app) 


# Error handeling
@app.errorhandler(400)
def handle_400_error(_error):
    return make_response(jsonify({'error': 'Kesalahan request'}), 400)


@app.errorhandler(401)
def handle_401_error(_error):
    return make_response(jsonify({'error': 'Tidak ada akses'}), 401)


@app.errorhandler(404)
def handle_404_error(_error):
    return make_response(jsonify({'error': 'Tidak ditemukan'}), 404)


@app.errorhandler(500)
def handle_500_error(_error):
  return make_response(jsonify({'error': 'Server error'}), 500)

  
def get_db():
  db = SessionLocal()
  try:
      return db
  finally:
      db.close()

@app.route("/")
def index():
    if (get_db()):
      return "Connected to database"
    else:
      return "Database is not connected"

@app.route("/get-all-sma", methods=["GET"])
def get_all_data_sma():
  return jsonify(controllers.get_all_sma(db=get_db()))

@app.route("/get-sma", methods=["GET"])
def get_sma():
  npsn = request.args.get("npsn")
  if npsn:
    sma = controllers.get_sma_by_npsn(db=get_db(), npsn=npsn)
    if sma is None:
      return make_response(jsonify({'error': 'Data tidak ditemukan!'}), 400)
    else:
      return jsonify(sma)
  else:
    kel = request.args.get('kel')
    kec = request.args.get('kec')
    if kel or kec:
      sma = controllers.get_sma_kel_kec(db=get_db(), kel=kel, kec=kec)
      if sma is None:
        return jsonify([])
      else:
        return sma
    else:
      return make_response(jsonify({'error': 'Kesalahan request.'}), 400)

@app.route("/get-nearest-sma", methods=["GET"])
def get_nearest_sma():
  lat = request.args.get('lat')
  lon = request.args.get('lon')
  if lat and lon:
    sma = controllers.get_sma_nearest(db=get_db(), lat=lat, lon=lon)
    return sma  
  else:
    return make_response(jsonify({'error': 'Kesalahan request.'}), 400)

# @app.route("/add-sma", methods=["POST"])
# def addDataSMA():
#   try:
#     cur = db.cursor()
#     json = request.json
#     data = { "akreditasi": json["akreditasi"],  }
#     alamat = data["alamat"]
#     jumlah_guru = data["jumlah_guru"]
#     jumlah_siswa = data["jumlah_siswa"]
#     kecamatan = data["kecamatan"]
#     kelurahan = data["kelurahan"]
#     kepala_sekolah = data["kepala_sekolah"]
#     latitude = data["latitude"]
#     longitude = data["longitude"]
#     nama_sekolah = data["nama_sekolah"]
#     telp_sekolah = data["telp_sekolah"]
#     npsn = data["npsn"]
#     cur.execute(f'''
#       SELECT * FROM data_sebaran_sekolah_sma WHERE npsn = '{npsn}';  
#     ''')
#     check_data = cur.fetchall()
#     if len(check_data) == 0:
#       cur.execute(f'''
#         INSERT INTO data_sebaran_sekolah_sma 
#         (npsn, akreditasi, alamat, jumlah_guru, jumlah_siswa, kecamatan, kelurahan, kepala_sekolah, latitude, longitude, nama_sekolah, telp_sekolah)
#         VALUES ('{npsn}', '{akreditasi}', '{alamat}', '{jumlah_guru}', {jumlah_siswa}, '{kecamatan}', '{kelurahan}', '{kepala_sekolah}', '{latitude}', '{longitude}', '{nama_sekolah}', '{telp_sekolah}');  
#       ''')
#     else:
#       raise Exception(f'Data sekolah dengan NPSN: {npsn} sudah terdaftar.')
#   except Exception as e:
#     print(e)
#     return ({"message": str(e)})
#   return jsonify({"message": f"Berhasil menambahkan data sekolah dengan NPSN: {npsn}"})

# @app.route("/update-sma", methods=["PUT"])
# def editDataSMA():
#   try:
#     cur = db.cursor()
#     data = request.json
#     akreditasi = data["akreditasi"]
#     alamat = data["alamat"]
#     jumlah_guru = data["jumlah_guru"]
#     jumlah_siswa = data["jumlah_siswa"]
#     kecamatan = data["kecamatan"]
#     kelurahan = data["kelurahan"]
#     kepala_sekolah = data["kepala_sekolah"]
#     latitude = data["latitude"]
#     longitude = data["longitude"]
#     nama_sekolah = data["nama_sekolah"]
#     telp_sekolah = data["telp_sekolah"]
#     npsn = data["npsn"]
#     cur.execute(f'''
#       SELECT * FROM data_sebaran_sekolah_sma WHERE npsn = '{npsn}';  
#     ''')
#     check_data = cur.fetchall()
#     if len(check_data) > 0:
#       cur.execute(f'''
#         UPDATE data_sebaran_sekolah_sma 
#         SET akreditasi = '{akreditasi}', alamat = '{alamat}', jumlah_guru = '{jumlah_guru}', jumlah_siswa = {jumlah_siswa}, kecamatan = '{kecamatan}', kelurahan = '{kelurahan}', kepala_sekolah = '{kepala_sekolah}', latitude = '{latitude}', longitude = '{longitude}', nama_sekolah = '{nama_sekolah}', telp_sekolah = '{telp_sekolah}'
#         WHERE npsn = '{npsn}';
#       ''')
#     else:
#       raise Exception(f'Data sekolah dengan NPSN: {npsn} tidak ada.')
#   except Exception as e:
#     print(e)
#     return ({"message": str(e)})
#   return jsonify({"message": f"Berhasil mengupdate data sekolah dengan NPSN: {npsn}"})

# @app.route("/delete-sma", methods=["DELETE"])
# def deleteDataSMA():
#   try:
#     cur = db.cursor()
#     npsn = request.args.get("npsn")
#     cur.execute(f'''
#       DELETE FROM data_sebaran_sekolah_sma 
#       WHERE npsn = '{npsn}';  
#     ''')
#   except Exception as e:
#     return ({"message": str(e)})
#   return jsonify({"message": f"Berhasil menghapus data sekolah dengan NPSN: {npsn}"})

if __name__ == '__main__':
  app.run(debug=True)