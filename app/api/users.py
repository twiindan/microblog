import datetime

from flask import jsonify, request, url_for, g, current_app
from flask_uploads import UploadSet, configure_uploads, IMAGES

from app import db
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request, error_response
from app.main.routes import IMAGE_ROUTE, IMAGE_CONVERTED_BIG, IMAGE_CONVERTED_LITTLE
from app.models import User, Message, Post


@bp.route('/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    return jsonify(User.query.get_or_404(id).to_dict())


@bp.route('/users', methods=['GET'])
@token_auth.login_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(User.query, page, per_page, 'api.get_users')
    return jsonify(data)


@bp.route('/users/<int:id>/followers', methods=['GET'])
@token_auth.login_required
def get_followers(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.followers, page, per_page,
                                   'api.get_followers', id=id)
    return jsonify(data)


@bp.route('/users/<int:id>/followed', methods=['GET'])
@token_auth.login_required
def get_followed(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.followed, page, per_page,
                                   'api.get_followed', id=id)
    return jsonify(data)


@bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    if 'username' not in data or 'email' not in data or 'password' not in data:
        return bad_request('must include username, email and password fields')
    if User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_user', id=user.id)
    return response


@bp.route('/users/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_user(id):

    user = User.query.get_or_404(id)
    if user == g.current_user:
        data = request.get_json() or {}
        if 'username' in data and data['username'] != user.username and \
                User.query.filter_by(username=data['username']).first():
            return bad_request('please use a different username')
        if 'email' in data and data['email'] != user.email and \
                User.query.filter_by(email=data['email']).first():
            return bad_request('please use a different email address')
        user.from_dict(data, new_user=False)
        db.session.commit()
        return jsonify(user.to_dict())
    else:
        return error_response(403, "You can only change your own user")


@bp.route('/logout')
@token_auth.login_required
def logout():
    g.current_user.revoke_token()
    db.session.commit()
    return '', 204


@bp.route('/follow/<int:id>', methods=['POST'])
@token_auth.login_required
def follow(id):
    user = User.query.get_or_404(id)
    if user == g.current_user:
        return error_response(400, "You cannot follow yourself!")
    g.current_user.follow(user)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = g.current_user.to_collection_dict(g.current_user.followed, page, per_page,
                                   'api.get_followers', id=g.current_user.id)
    return jsonify(data)


@bp.route('/unfollow/<int:id>', methods=['POST'])
@token_auth.login_required
def unfollow(id):
    user = User.query.get_or_404(id)
    if user == g.current_user:
        return error_response(400, "You cannot follow yourself!")
    g.current_user.unfollow(user)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = g.current_user.to_collection_dict(g.current_user.followed, page, per_page,
                                   'api.get_followers', id=g.current_user.id)
    return jsonify(data)


@bp.route('/messages')
@token_auth.login_required
def get_messages():
    user = g.current_user
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Message.to_collection_dict(user.messages_received, page, per_page,
                                   'api.get_messages')
    return jsonify(data)


@bp.route('/<int:id>/message', methods=['POST'])
@token_auth.login_required
def send_message(id):
    data = request.get_json() or {}
    current_user = g.current_user
    user = User.query.get_or_404(id)
    if user == current_user:
        return error_response(400, "Yoy cannot send messages to you. Please make friends")
    message = Message(recipient_id=id, sender_id=current_user.id, body=data['body'])
    db.session.add(message)
    db.session.commit()
    response = jsonify(message.to_dict())
    response.status_code = 201
    return response


@bp.route('/<int:id>/posts')
@token_auth.login_required
def get_user_posts(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.posts, page, per_page,
                                   'api.get_user_posts', id=id)
    return jsonify(data)


@bp.route('/post', methods=['POST'])
@token_auth.login_required
def create_post():
    user = g.current_user
    data = request.get_json() or {}
    post = Post(user_id=user.id, body=data['body'])
    db.session.add(post)
    db.session.commit()
    response = jsonify(post.to_dict())
    response.status_code = 201
    return response

@bp.route('/explore')
@token_auth.login_required
def explore():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(Post.query.order_by(Post.timestamp.desc()), page, per_page,
                                   'api.explore')

    return jsonify(data)


@bp.route('/upload', methods=['POST'])
@token_auth.login_required
def upload_image():
    current_app.config['UPLOADED_PHOTOS_DEST'] = IMAGE_ROUTE
    photos = UploadSet('photos', IMAGES)
    configure_uploads(current_app, photos)
    filename = photos.save(request.files['photo'])
    resize_image(filename, g.current_user.username)
    return 'uploaded'

def resize_image(filename, username):
    from PIL import Image
    original_image = Image.open(IMAGE_ROUTE + '/' + filename)
    resized_image = original_image.resize((128, 128))
    resized_image.save(IMAGE_CONVERTED_BIG + username + '.png')
    resized_image = original_image.resize((64, 64))
    resized_image.save(IMAGE_CONVERTED_LITTLE + username + '.png')
