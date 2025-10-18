import os
import hashlib
from flask import (
    Flask, jsonify, request, make_response,
    render_template, send_file, send_from_directory,
    abort, g, redirect, make_response
)
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
import jwt
from jwt import InvalidTokenError
from models import PackMetadata
from packs import PackCache
from pydantic import ValidationError

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "changeme")
PACKS_DIR = "packs"

app = Flask(__name__, static_folder="static")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)

packs = PackCache(PACKS_DIR)
packs.load()


@app.before_request
def load_user_from_jwt():
    g.authenticated = False
    token = request.cookies.get('jwt')
    if token:
        try:
            jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            g.authenticated = True
        except InvalidTokenError:
            pass


@app.route('/')
def index():
    main_pack = packs.get_main()
    return redirect(f'/p/{main_pack.slug}')


def create_pack_response(pack: PackMetadata, max_age: float):
    zip_path = packs.get_zip_path(pack.slug)
    if not os.path.exists(zip_path):
        return {"error": "Pack zip file is deleted"}, 404
    response = make_response(send_file(zip_path, as_attachment=True, download_name=f"{pack.name}-{pack.slug}.zip", max_age=max_age))
    if max_age == 0:
        # Explicitly disable caching
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.route('/p/<slug>/dl', methods=['GET'])
def pack_detail_download(slug):
    pack = packs.get(slug)
    if not pack:
        return {"error": "Pack not found"}, 404

    return create_pack_response(pack, 86400)


def is_direct_download():
    # Override so dl=0 can be specified to force it to work
    if 'dl' in request.args:
        return request.args.get("dl") == "1"

    # When this url instead of the /dl url is specified, this handles the Minecraft client
    # downloading it. Everyone else (browsers) get to see the detail page.
    if 'X-Minecraft-Version' in request.headers or 'X-Minecraft-Version-Id' in request.headers:
        return True

    # Convenience: when downloading with wget or curl, download the zip instead
    # If server admins run this on a box, that allows for easier installing
    user_agent = request.headers.get('User-Agent', '')
    for prefix in ['wget/', 'wget2/', 'curl/', 'aria2/', 'fetch/']:
        if user_agent.startswith(prefix):
            return True

    return False


@app.route('/p/<slug>', methods=['GET'])
def pack_detail(slug):
    pack = packs.get(slug)
    if not pack:
        return {"error": "Pack not found"}, 404

    if is_direct_download():
        # Note: no caching, as this url is dynamic
        return create_pack_response(pack, 0)

    return render_template("pack.html",
                           authenticated=g.authenticated,
                           pack=pack,
                           main_packs=packs.get_main_packs())


@app.route("/p/<slug>", methods=["PATCH"])
def pack_update_detail(slug):
    pack = packs.get(slug)
    if not pack:
        return {"error": "Pack not found"}, 404

    try:
        # Parse incoming JSON
        incoming_data = request.get_json()
        if not incoming_data:
            return jsonify({"error": "Missing JSON body"}), 400

        # Merge using Pydantic's model_copy(update=...)
        packs.update(PackMetadata.model_validate({**pack.model_dump(), **incoming_data}))

        return jsonify({"status": "OK"}), 200
    except ValidationError as ve:
        return jsonify({"error": "Validation failed", "details": ve.errors()}), 422
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/p/<slug>/duplicate', methods=['POST'])
def pack_duplicate(slug):
    if not g.authenticated:
        return {"error": "Unauthorized"}, 401

    pack_meta = packs.get(slug)
    if not pack_meta:
        return {"error": "Pack not found"}, 404

    new_pack_meta = packs.duplicate(pack_meta)
    return {"redirect_url": f"/p/{new_pack_meta.slug}"}, 200


@app.route('/p/<slug>/upload', methods=['POST'])
def pack_upload_zip(slug):
    if not g.authenticated:
        return {"error": "Unauthorized"}, 401

    pack_meta = packs.get(slug)
    if not pack_meta:
        return {"error": "Pack not found"}, 404

    zip_file = request.files.get('file')
    if not zip_file:
        return {"error": "Missing zip file"}, 400

    zip_data = zip_file.read()
    zip_sha1 = hashlib.sha1(zip_data).hexdigest()
    if pack_meta.sha1 == zip_sha1 and packs.is_zip_equal(pack_meta.slug, zip_data):
        return {"error": "This zip file is already configured"}

    # All good. Save the file to disk and swap the old meta out for a new one,
    # with a new slug (and so pointing to the new file). Also make it the new
    # main entry.
    new_pack_meta = packs.save_new_zip(pack_meta, zip_data, zip_sha1)
    return {"redirect_url": f"/p/{new_pack_meta.slug}"}, 200


@app.route('/authenticate', methods=['POST'])
def auth_check():
    data = request.get_json()
    token = data.get('token', '')
    try:
        jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except InvalidTokenError as e:
        return jsonify({'error': 'Invalid token', 'details': str(e)}), 401

    response = make_response(jsonify({'success': True}))
    response.set_cookie(
        'jwt', token,
        httponly=True,
        secure=True,
        samesite='Strict',
        path='/'
    )
    return response


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)

