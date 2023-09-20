import asyncio
import uuid
import httpx
import markupsafe
from flask import url_for, render_template, flash, send_from_directory, redirect, session, Blueprint, request, abort
from werkzeug.utils import secure_filename
import os
from rembg import remove
from PIL import UnidentifiedImageError
from werkzeug.security import safe_join
from wtforms import FileField, SubmitField
from flask_wtf.file import FileAllowed
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired

main = Blueprint('main', __name__)
main.secret_key = os.urandom(32)
allow_extension = ['png', 'jpeg', 'jpg']
UPLOAD_FOLDER = 'static/upload'



class UploadImage(FlaskForm):
    image = FileField('image', validators=[
        FileAllowed(allow_extension, 'Extension not allowed.'),
        DataRequired('Please choose a file to upload.')
    ])
    submit = SubmitField('Submit')


def remove_bg(image_content: bytes):
    try:
        r_image = remove(image_content)

        return r_image
    except UnidentifiedImageError:
        return False


def generate_unique_filename(file_name: str):
    if '.' in file_name:
        extension = os.path.splitext(file_name)[1]
        new_name = f'{uuid.uuid4()}{extension}'
        return new_name
    return False


@main.get('/')
def index():
    form = UploadImage()
    return render_template('index.html', form=form)


@main.post('/upload')
def upload_image():
    form = UploadImage()

    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'danger')
        return redirect(url_for('main.index'))

    file = form.image.data
    file_name = secure_filename(file.filename)
    file_name = generate_unique_filename(file_name)

    processed_image = remove_bg(file.read())
    if not processed_image:
        flash('Sorry, we could not process the uploaded image. Please make sure it is a valid image file. and that '
              'you have background to remove', 'danger')
        return redirect(url_for('main.index'))

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    processed_file_path = safe_join(UPLOAD_FOLDER, file_name)

    with open(processed_file_path, 'wb') as processed_file:
        processed_file.write(processed_image)

    processed_image_url = url_for('main.uploaded_image', filename=file_name)
    download_link = markupsafe.Markup(
        f'<a href="{processed_image_url}" download="{file_name}">Download Processed Image</a>')

    image_tag = markupsafe.Markup(f'<img src="{processed_image_url}" alt="Processed Image" width="200">')

    links = session.get('downloads_links', [])
    links.append(processed_image_url)
    session['downloads_links'] = links

    flash(f'Processed image saved at: {download_link}<br>{image_tag}', 'success')
    return redirect(url_for('main.index'))


@main.get('/history')
def history():
    links = session.get('downloads_links', [])
    return render_template('history.html', links=links)


@main.route('/uploads/<filename>')
def uploaded_image(filename: str):
    user_links: list[str] = session.get('downloads_links', [])
    if any(link.endswith(filename) for link in user_links):
        return send_from_directory(UPLOAD_FOLDER, filename)
    else:
        abort(403)


def add_cache_headers(response):
    cache_timeout = 3600
    response.headers['Cache-Control'] = f'public, max-age={cache_timeout}'
    return response


main.after_request(add_cache_headers)
