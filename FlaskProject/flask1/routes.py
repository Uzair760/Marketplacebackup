import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flask1 import app, db, bcrypt, mail
from flask1.forms import RegistrationForm, LoginForm, UpdateProfileDetails, PostListing, RequestResetForm, ResetPasswordForm
from flask1.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', title='Marketplace', posts=posts)

@app.route("/about")
def about():
    return render_template('about.html', title='About Page')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'{form.username.data} has created an account. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Create an Account', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f'{form.username.data} has logged in.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Username or password is incorrect.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    if current_user.image_file != 'default1.jpg':
        os.remove(os.path.join(app.root_path, 'static/images', current_user.image_file))
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/images', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

def save_item_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/images', picture_fn)
    form_picture.save(picture_path)

    return picture_fn

@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileDetails()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='images/' + current_user.image_file)
    return render_template('profile.html', title='Profile Page', image_file=image_file, form=form)

@app.route("/listing_new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostListing()
    if form.validate_on_submit():
        post = Post(item=form.item.data, desc=form.desc.data, price=form.price.data, seller=current_user)
        if form.item_picture.data:
            picture_file = save_item_picture(form.item_picture.data)
            post.item_image_file = picture_file
        db.session.add(post)
        db.session.commit()
        flash('You have listed your item.', 'success')
        return redirect(url_for('home'))
    return render_template('create_listing.html', title='Sell an Item', form=form, legend='Sell an Item')

@app.route("/listing_<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.item, post=post)

@app.route("/listing/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.seller != current_user:
        abort(403)
    form = PostListing()
    if form.validate_on_submit():
        post.item = form.item.data
        post.desc = form.desc.data
        post.price = form.price.data
        if form.item_picture.data:
            picture_file = save_item_picture(form.item_picture.data)
            post.item_image_file = picture_file
        db.session.commit()
        flash('The listing has been updated.', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.item.data = post.item
        form.desc.data = post.desc
        form.price.data = post.price
    return render_template('create_listing.html', title='Update Listing', form=form, legend='Update Listing')

@app.route("/listing/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.seller != current_user:
        abort(403)
    if post.item_image_file != 'default2.jpg':
        os.remove(os.path.join(app.root_path, 'static/images', post.item_image_file))
    db.session.delete(post)
    db.session.commit()
    flash('The listing has been removed.', 'message')
    return redirect(url_for('home'))

@app.route("/user_<string:username>")
def user_listings(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(seller=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_listings.html', title=f'{ username } listings', posts=posts, user=user)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='noreply@marketplace.com', recipient=[user.email])
    msg.body = f'''To reset your password, click the following link:
{url_for('reset_token', token=token, _external=True)}

This link will expire in { expires_sec } seconds.

Ignore this email if you did not make this request.
    '''
    mail.send(msg)

@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_form.html', title='Reset Password', form=form)

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('Invalid or expired token.', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf8')
        user.password = hashed_password
        db.session.commit()
        flash('The password has been changed. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)
