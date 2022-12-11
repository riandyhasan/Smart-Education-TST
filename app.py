from flask import Flask, jsonify, request, make_response, session
from flask_pydantic import validate
from flask_mail import Mail, Message
import pyotp
import controllers, models, schemas
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from datetime import datetime, timedelta
import jwt
from functools import wraps
from flask_mail import Mail, Message
import time

app = Flask(__name__)
# CONFIGS
#JWT
app.config['SECRET_KEY'] = 'vIpMWhXXrRLQR5Dze2GTKozaTLAZeLMt'
# MAIL
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'smarteducationtst@gmail.com'
app.config['MAIL_PASSWORD'] = 'jkdvdweqmjwvknao'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)
totp = pyotp.TOTP('WUXOZ4AB7CFP6ZDH5KSUSIRTFWZ2BOTC', interval=60)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
        if not token:
            return jsonify({'error' : 'Memerlukan akses token.'}), 401
  
        try:
          token = token.replace('Bearer ', '')
          data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
          current_user = controllers.get_user_by_id(db=get_db(), id=data['user_id'])
        except:
          return make_response(jsonify({'error' : 'Token invalid!'}), 401)
        return  f(current_user.serialize(), *args, **kwargs)
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

@app.route("/signup", methods=['POST'])
@validate()
def signup(body: schemas.CreateUser):
  db = db=get_db()
  if controllers.get_user_by_username(db=db, username=body.username):
    return make_response(jsonify({'error': 'Username telah terdaftar. Silahklan login.'}), 400)
  if controllers.get_user_by_email(db=db, email=body.email):
    return make_response(jsonify({'error': 'Email telah terdaftar.'}), 400)
  user = controllers.add_user(db=db, user=body)
  msg = Message(
    'Smart Education - Highschool Recommendation',
    sender = app.config['MAIL_USERNAME'],
    recipients = [user.email]
  )
  user_otp = totp.now()
  msg.body = f'Kode OTP Anda adalah: {user_otp}. Mohon untuk tidak berikan Kode OTP Anda ke siapapun! Kode ini akan berlaku selama 1 menit.'
  mail.send(msg)
  return jsonify({'success': 'Berhasil membuat akun. Silahkan verifikasi OTP.'})

@app.route("/signin", methods=['POST'])
@validate()
def signin(body: schemas.LoginUser):
  user = controllers.get_user_by_username(db=get_db(), username=body.username)
  if user is None:
    return make_response(jsonify({'error': 'Username atau password salah.'}), 400)
  if user.password != controllers.hash_password(body.password):
    return make_response(jsonify({'error': 'Username atau password salah.'}), 400)
  msg = Message(
    'Smart Education - Highschool Recommendation',
    sender = app.config['MAIL_USERNAME'],
    recipients = [user.email]
    )
  user_otp = totp.now()
  msg.body = f'Kode OTP Anda adalah: {user_otp}. Mohon untuk tidak berikan Kode OTP Anda ke siapapun! Kode ini akan berlaku selama 1 menit.'
  mail.send(msg)
  return jsonify({'success': 'Login berhasil. Silahkan verifikasi OTP.'})

@app.route("/verify-otp", methods=['GET'])
@validate()
def verify_otp(body: schemas.UserOTP):
  user = controllers.get_user_by_username(db=get_db(), username=body.username)
  if not user:
    return make_response(jsonify({'error': 'Akun tidak ada.'}), 401)
  if totp.verify(body.otp):
    token = jwt.encode({
              'user_id': user.id,
              'exp' : datetime.utcnow() + timedelta(minutes = 60)
          }, app.config['SECRET_KEY'])
    return jsonify({'access_token': token})
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
    return jsonify({'success': 'Berhasil memverifikasi user.'})
  return make_response(jsonify({'error': 'Kesalahan pada server!'}), 500)

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
  lon = request.args.get('lon')
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

if __name__ == '__main__':
  app.run(debug=True)