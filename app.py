from flask import Flask, jsonify, request, make_response, render_template, redirect
from flask_pydantic import validate
from flask_mail import Mail, Message
import pyotp
import controllers, models, schemas
from sqlalchemy.orm import Session
from database import SessionLocal
from datetime import datetime, timedelta
import jwt
from functools import wraps
import os
from dotenv import load_dotenv
import logging
import requests

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
# Load environment variables
load_dotenv()
# CONFIGS
#JWT
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
# MAIL
app.config['MAIL_SERVER']= os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT') 
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME') 
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD') 
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

PARTNER_API = 'http://20.24.70.52'

mail = Mail(app)
totp = pyotp.TOTP(os.getenv('TOTP_KEY') , interval=120)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
        if not token:
            return make_response(jsonify({'error' : 'Memerlukan akses token.'}), 401)
        try:
          token = token.replace('Bearer ', '')
          data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
          current_user = controllers.get_user_by_id(db=get_db(), id=data['user_id'])
        except Exception as e:
          if(str(e) == 'Signature has expired'):
            return make_response(jsonify({'error' : 'Session telah berakhir! Mohon masuk kembali.'}), 401)  
          return make_response(jsonify({'error' : 'Token invalid!'}), 401)
        return f(current_user.serialize(), *args, **kwargs)
    return decorated

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
  return make_response(jsonify({'error': 'Server error.'}), 500)

  
def get_db():
  db = SessionLocal()
  try:
      return db
  finally:
      db.close()

@app.route("/")
def index():
  return render_template("index.html")

@app.route("/register")
def register():
  return render_template("signup.html")

@app.route("/otp")
def otp():
  return render_template("otp.html")

@app.route("/user-input")
def user_input():
  return render_template("userinput.html")

@app.route("/signup", methods=['POST'])
# @validate()
def signup():
  try:
    body = request.form
    db = db=get_db()
    if controllers.get_user_by_username(db=db, username=body['username']):
      return make_response(jsonify({'error': 'Username telah terdaftar. Silahklan login.'}), 400)
    if controllers.get_user_by_email(db=db, email=body['email']):
      return make_response(jsonify({'error': 'Email telah terdaftar.'}), 400)
    user = controllers.add_user(db=db, user=body)
    msg = Message(
      'Smart Education - Highschool Recommendation',
      sender = app.config['MAIL_USERNAME'],
      recipients = [user.email]
    )
    user_otp = totp.now()
    msg.body = f'Kode OTP Anda adalah: {user_otp}. Mohon untuk tidak berikan Kode OTP Anda ke siapapun! Kode ini akan berlaku selama 2 menit.'
    mail.send(msg)
  except Exception as e:
    return jsonify(str(e)), 500
  return redirect('/otp')

@app.route("/signin", methods=['POST'])
# @validate()
def signin():
  body = request.form
  user = controllers.get_user_by_username(db=get_db(), username=body['username'])
  if user is None:
    return make_response(jsonify({'error': 'Username atau password salah.'}), 400)
  if user.password != controllers.hash_password(body['password']):
    return make_response(jsonify({'error': 'Username atau password salah.'}), 400)
  msg = Message(
    'Smart Education - Highschool Recommendation',
    sender = app.config['MAIL_USERNAME'],
    recipients = [user.email]
    )
  user_otp = totp.now()
  msg.body = f'Kode OTP Anda adalah: {user_otp}. Mohon untuk tidak berikan Kode OTP Anda ke siapapun! Kode ini akan berlaku selama 2 menit.'
  mail.send(msg)
  return redirect('/otp')

@app.route("/signin-without-otp", methods=["POST"])
@validate()
def signin_no_otp(body: schemas.LoginUser):
  user = controllers.get_user_by_username(db=get_db(), username=body.username)
  if user is None:
    return make_response(jsonify({'error': 'Username atau password salah.'}), 400)
  if user.password != controllers.hash_password(body.password):
    return make_response(jsonify({'error': 'Username atau password salah.'}), 400)
  token = jwt.encode({
      'user_id': user.id,
      'exp' : datetime.utcnow() + timedelta(minutes = 60)
  }, app.config['SECRET_KEY'])
  return jsonify({'access_token': token})

@app.route("/verify-otp", methods=['GET', 'POST'])
def verify_otp():
  body = request.form
  user = controllers.get_user_by_username(db=get_db(), username=body['username'])
  if not user:
    return make_response(jsonify({'error': 'Akun tidak ada.'}), 401)
  if totp.verify(body['otp']):
    token = jwt.encode({
              'user_id': user.id,
              'exp' : datetime.utcnow() + timedelta(minutes = 60)
          }, app.config['SECRET_KEY'])
    return redirect('/user-input')
  return make_response(jsonify({'error': 'OTP Salah.'}), 401)

@app.route("/verify-user", methods=['PUT'])
@token_required
@validate()
def verify_user(user, query: schemas.UserVerification):
  db = get_db()
  db_user = controllers.get_user_by_id(db=db, id=query.user_id)
  if not db_user:
    return make_response(jsonify({'error': 'Akun tidak ada.'}), 401)
  if not user['admin']:
    return make_response(jsonify({'error': 'Akun tidak memiliki kuasa.'}), 401)
  if controllers.verify_user(db=db, user=db_user):
    return jsonify({'success': 'Berhasil memverifikasi akun.'})
  return make_response(jsonify({'error': 'Kesalahan server.'}), 500)

@app.route("/get-all-sma", methods=["GET"])
@token_required
def get_all_data_sma(user):
  if user['terverifikasi']:
    return jsonify(controllers.get_all_sma(db=get_db()))
  return make_response(jsonify({'error': 'Akun belum terverifikasi.'}), 401)

@app.route("/get-sma", methods=["GET"])
@token_required
@validate()
def get_sma(user, query: schemas.QuerySMA):
  if (not user['terverifikasi']):
    return make_response(jsonify({'error': 'Akun belum terverifikasi.'}), 401)
  npsn = query.npsn
  if npsn:
    sma = controllers.get_sma_by_npsn(db=get_db(), npsn=npsn)
    if sma is None:
      return make_response(jsonify({'error': 'Data tidak ditemukan!'}), 400)
    else:
      return jsonify(sma)
  else:
    kel = query.kel
    kec = query.kec
    if kel or kec:
      sma = controllers.get_sma_kel_kec(db=get_db(), kel=kel, kec=kec)
      if sma is None:
        return jsonify([])
      else:
        return sma
    else:
      return make_response(jsonify({'error': 'Kesalahan request.'}), 400)

@app.route("/get-nearest-sma", methods=["GET"])
@token_required
@validate()
def get_nearest_sma(user, query: schemas.Coordinate):
  if (not user['terverifikasi']):
    return make_response(jsonify({'error': 'Akun belum terverifikasi.'}), 401)
  lat = query.lat
  lon = query.lon
  if lat and lon:
    sma = controllers.get_sma_nearest(db=get_db(), lat=lat, lon=lon)
    return sma  
  else:
    return make_response(jsonify({'error': 'Kesalahan request.'}), 400)

@app.route("/add-sma", methods=["POST"])
@token_required
@validate()
def add_data_sma(user, body: schemas.CreateSMA):
  if (not user['terverifikasi']):
    return make_response(jsonify({'error': 'Akun belum terverifikasi.'}), 401)
  if request.method == 'POST':
    db = get_db()
    db_sma = controllers.get_sma_by_npsn(db=db, npsn=body.npsn)
    if db_sma:
      return make_response(jsonify({'error': 'SMA telah terdaftar di database.'}), 400)
    try:
      sma = controllers.add_sma(db=db, sma=body)
      if sma:
        return make_response(jsonify({'message': f'Berhasil menambahkan SMA dengan NPSN {body.npsn}.'}), 200)
      else:
        return make_response(jsonify({'error': 'Server error.'}), 500)
    except Exception:
      return make_response(jsonify({'error': 'Server error.'}), 500)
  else:
    return make_response(jsonify({'error': 'Kesalahan request method.'}), 400)

@app.route("/update-sma", methods=["PUT"])
@token_required
@validate()
def edit_data_sma(user, body: schemas.UpdateSMA):
  if (not user['terverifikasi']):
    return make_response(jsonify({'error': 'Akun belum terverifikasi.'}), 401)
  if request.method == 'PUT':
    db = get_db()
    db_sma = controllers.edit_sma(db=db, sma=body)
    if db_sma:
      return make_response(jsonify({'message': f'Berhasil mengedit SMA dengan NPSN {body.npsn}.'}), 200)
    else:
      return make_response(jsonify({'error': 'SMA tidak ada di database.'}), 400)
  else:
    return make_response(jsonify({'error': 'Kesalahan request method.'}), 400)

@app.route("/delete-sma", methods=["DELETE"])
@token_required
def delete_data_sma(user):
  if (not user['terverifikasi']):
    return make_response(jsonify({'error': 'Akun belum terverifikasi.'}), 401)
  npsn = request.args.get("npsn")
  if request.method == "DELETE":
    try:
      deleted_sma = controllers.delete_sma(db=get_db(), npsn=npsn)
      if deleted_sma:
        return make_response(jsonify({'message': f'Berhasil menghapus SMA dengan NPSN {npsn}.'}), 200)
      else:
        return make_response(jsonify({'error': 'SMA tidak ada di database.'}), 400)
    except Exception:
        return make_response(jsonify({'error': 'Server error'}), 500)
  else:
    return make_response(jsonify({'error': 'Kesalahan request method.'}), 400)

@app.route("/get-recommendation", methods=["GET", "POST"])
@validate()
def get_recomendation():
  recommendation = []
  data = request.form
  lat = data['lat']
  lon = data['lon']
  if lat and lon:
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = {
      'username': 'riandyhsn',
      'password': 'password'
    }
    response_login = requests.post(PARTNER_API+'/signin-without-otp', headers=headers, json=data)
    token = response_login.json()['access_token']
    try:
      point = {'lat': lat, 'lon': lon}
      sma = controllers.get_sma_nearest(db=get_db(), lat=lat, lon=lon)
      headers = {
              'accept': 'application/json',
              'Content-Type': 'application/json',
              'Authorization': 'Bearer ' + token
          }
      current_kel = None
      data_kel = [] 
      for _ in sma:
        if _['kelurahan'] != current_kel:
          current_kel = _['kelurahan']
          query = '/get-kelurahan?nama_kelurahan=' + current_kel
          response = requests.get(PARTNER_API+query, headers=headers)
          data_kel.append(controllers.get_penduduk_kelurahan(response.json()))
        point2 = {'lat': _['latitude'], 'lon': _['longitude']}
        recommendation.append({ 
          'nama_sekolah': _['nama_sekolah'], 
          'alamat': _['alamat'], 
          'jarak': controllers.calculate_jarak(point, point2), 
          'akreditasi': _['akreditasi'],
          'keketatan': controllers.calculate_keketatan(_, data_kel) 
          })
      recommendation = controllers.sort_recommendations(recommendation)
      res = []
      i = 0
      for r in recommendation:
        if i < 3:
          res.append(r) 
        else:
          break
        i += 1
      print(res)
      return render_template("recommendation.html", data=res)
    except Exception as e:
      print(e)
      return make_response(jsonify({'error': 'Server error.'}), 500)
  else:
    return make_response(jsonify({'error': 'Kesalahan request.'}), 400)

if __name__ == '__main__':
  app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))