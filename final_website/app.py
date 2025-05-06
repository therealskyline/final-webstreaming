import os
import re
import json
import logging
import datetime
import shutil
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import urllib.parse

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")

# Initialize database
# Utiliser SQLite en attendant de résoudre les problèmes avec PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///anime.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # Nouvelles colonnes pour stocker les préférences utilisateur
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Modèle pour suivre la progression des utilisateurs sur les animes
class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    anime_id = db.Column(db.Integer, nullable=False)
    season_number = db.Column(db.Integer, nullable=False)
    episode_number = db.Column(db.Integer, nullable=False)
    time_position = db.Column(db.Float, default=0)  # Position en secondes dans l'épisode
    completed = db.Column(db.Boolean, default=False)
    last_watched = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relation avec l'utilisateur
    user = db.relationship('User', backref=db.backref('progress', lazy='dynamic'))

    # Contrainte d'unicité pour éviter les doublons
    __table_args__ = (
        db.UniqueConstraint('user_id', 'anime_id', 'season_number', 'episode_number'),
    )

# Modèle pour les favoris des utilisateurs
class UserFavorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    anime_id = db.Column(db.Integer, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relation avec l'utilisateur
    user = db.relationship('User', backref=db.backref('favorites', lazy='dynamic'))

    # Contrainte d'unicité pour éviter les doublons
    __table_args__ = (
        db.UniqueConstraint('user_id', 'anime_id'),
    )

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Load anime data from JSON file
def load_anime_data():
    try:
        with open('static/data/anime.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure we're getting a dictionary with an anime key
            if isinstance(data, dict) and 'anime' in data:
                return data['anime']
            elif isinstance(data, list):
                # If it's just a list (no wrapper), return it directly
                return data
            else:
                # Create a default structure
                logger.warning("Anime data file has unexpected format. Creating default structure.")
                return []
    except FileNotFoundError:
        logger.error("Anime data file not found. Creating empty data file.")
        # Create empty data file with proper structure
        os.makedirs('static/data', exist_ok=True)
        with open('static/data/anime.json', 'w', encoding='utf-8') as f:
            json.dump({'anime': []}, f, indent=4)
        return []
    except json.JSONDecodeError:
        logger.error("Error decoding anime data file. Returning empty list.")
        return []

def save_anime_data(data):
    try:
        os.makedirs('static/data', exist_ok=True)
        # Ensure we're saving with the expected structure
        if isinstance(data, list):
            save_data = {'anime': data}
        else:
            # If somehow data is not a list, create a default structure
            logger.warning("Unexpected data format when saving anime data")
            save_data = {'anime': []}

        with open('static/data/anime.json', 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving anime data: {e}")
        return False

# Extract unique genres from anime data
def get_all_genres():
    anime_data = load_anime_data()
    genres = set()
    for anime in anime_data:
        for genre in anime.get('genres', []):
            genres.add(genre.lower())
    return sorted(list(genres))

# Helper function to extract Google Drive ID from URL
def extract_drive_id(url):
    # Looking for patterns like drive.google.com/file/d/ID/view
    drive_patterns = [
        r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)'
    ]

    for pattern in drive_patterns:
        match = re.search(pattern, url)
        if match:
            logger.debug(f"Extracted Google Drive ID: {match.group(1)}")
            return match.group(1)

    # If it's just the ID itself
    if not url.startswith(('http://', 'https://')):
        logger.debug(f"Using provided ID: {url}")
        return url

    # If it contains the ID in the URL but doesn't match the patterns above
    parts = url.split('/')
    for part in parts:
        if len(part) > 20 and re.match(r'^[a-zA-Z0-9_-]+$', part):
            logger.debug(f"Extracted potential Google Drive ID from parts: {part}")
            return part

    logger.warning(f"Could not extract Google Drive ID from URL: {url}")
    return None

@app.route('/')
def index():
    # Rediriger vers la page de connexion si l'utilisateur n'est pas connecté
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    anime_data = load_anime_data()

    # Récupérer les animes en cours de visionnage
    continue_watching = []
    if current_user.is_authenticated:
        # Récupérer les progressions non terminées les plus récentes par anime
        latest_progress_by_anime = UserProgress.query.filter_by(
            user_id=current_user.id
        ).order_by(
            UserProgress.last_watched.desc()
        ).all()

        # Pour chaque anime, trouver les données et ajouter à la liste
        processed_animes = set()
        for progress in latest_progress_by_anime:
            if progress.anime_id not in processed_animes:
                anime = next((a for a in anime_data if int(a.get('id', 0)) == progress.anime_id), None)
                if anime:
                    # Trouver la saison et l'épisode correspondants
                    season = next((s for s in anime.get('seasons', []) if s.get('season_number') == progress.season_number), None)
                    if season:
                        episode = next((e for e in season.get('episodes', []) if e.get('episode_number') == progress.episode_number), None)
                        if episode:
                            continue_watching.append({
                                'anime': anime,
                                'progress': progress,
                                'season': season,
                                'episode': episode
                            })
                            processed_animes.add(progress.anime_id)

    # Récupérer les favoris
    favorite_anime = []
    if current_user.is_authenticated:
        favorites = UserFavorite.query.filter_by(user_id=current_user.id).all()
        for favorite in favorites:
            anime = next((a for a in anime_data if a.get('id') == favorite.anime_id), None)
            if anime:
                favorite_anime.append(anime)

    # Filter featured anime for the homepage
    featured_anime = [anime for anime in anime_data if anime.get('featured', False)]

    return render_template('index_new.html', 
                       anime_list=featured_anime,
                       continue_watching=continue_watching,
                       favorite_anime=favorite_anime)

@app.route('/search')
@login_required
def search():
    query = request.args.get('query', '').lower()
    genre = request.args.get('genre', '').lower()

    anime_data = load_anime_data()
    filtered_anime = []

    for anime in anime_data:
        title_match = query in anime.get('title', '').lower()
        genre_match = not genre or genre in [g.lower() for g in anime.get('genres', [])]

        if (not query or title_match) and genre_match:
            filtered_anime.append(anime)

    return render_template('search.html', 
                           anime_list=filtered_anime, 
                           query=query, 
                           selected_genre=genre, 
                           genres=get_all_genres())

@app.route('/anime/<int:anime_id>')
@login_required
def anime_detail(anime_id):
    anime_data = load_anime_data()

    # Find the anime by ID (anime_id est un int, assurons-nous de comparer avec des int)
    anime = next((a for a in anime_data if int(a.get('id', 0)) == anime_id), None)

    if not anime:
        return render_template('404.html'), 404

    # Vérifier si l'anime est dans les favoris de l'utilisateur
    is_favorite = False
    episode_progress = {}
    latest_progress = None

    if current_user.is_authenticated:
        # Vérifier le statut favori
        favorite = UserFavorite.query.filter_by(
            user_id=current_user.id,
            anime_id=anime_id
        ).first()
        is_favorite = favorite is not None

        # Récupérer la progression pour tous les épisodes de cet anime
        progress_data = UserProgress.query.filter_by(
            user_id=current_user.id,
            anime_id=anime_id
        ).all()

        # Créer un dictionnaire de progression pour un accès facile dans le template
        for progress in progress_data:
            key = f"{progress.season_number}_{progress.episode_number}"
            episode_progress[key] = {
                'time_position': progress.time_position,
                'completed': progress.completed,
                'last_watched': progress.last_watched
            }

        # Trouver le dernier épisode regardé pour cet anime
        latest_progress = UserProgress.query.filter_by(
            user_id=current_user.id,
            anime_id=anime_id,
            completed=False
        ).order_by(
            UserProgress.last_watched.desc()
        ).first()

    return render_template('anime_new.html', 
                          anime=anime, 
                          is_favorite=is_favorite,
                          episode_progress=episode_progress,
                          latest_progress=latest_progress)

@app.route('/player/<int:anime_id>/<int:season_num>/<int:episode_num>')
@login_required
def player(anime_id, season_num, episode_num):
    anime_data = load_anime_data()

    # Find the anime by ID (même logique de conversion que anime_detail)
    anime = next((a for a in anime_data if int(a.get('id', 0)) == anime_id), None)

    if not anime:
        logger.error(f"Anime with ID {anime_id} not found")
        return render_template('404.html'), 404

    # Find the season
    season = next((s for s in anime.get('seasons', []) if s.get('season_number') == season_num), None)

    if not season:
        logger.error(f"Season {season_num} not found for anime {anime_id}")
        return render_template('404.html'), 404

    # Find the episode
    episode = next((e for e in season.get('episodes', []) if e.get('episode_number') == episode_num), None)

    if not episode:
        logger.error(f"Episode {episode_num} not found for anime {anime_id}, season {season_num}")
        return render_template('404.html'), 404

    # Generate download URL for Google Drive
    video_url = episode.get('video_url', '')
    file_id = extract_drive_id(video_url)
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}" if file_id else "#"

    logger.debug(f"Generated download URL: {download_url}")

    # Si l'utilisateur est connecté, récupérer sa progression et statut favori
    time_position = 0
    is_favorite = False

    if current_user.is_authenticated:
        # Récupérer la progression
        progress = UserProgress.query.filter_by(
            user_id=current_user.id,
            anime_id=anime_id,
            season_number=season_num,
            episode_number=episode_num
        ).first()

        if progress:
            time_position = progress.time_position

        # Vérifier si l'anime est dans les favoris
        favorite = UserFavorite.query.filter_by(
            user_id=current_user.id,
            anime_id=anime_id
        ).first()

        is_favorite = favorite is not None

    return render_template('player.html', 
                         anime=anime, 
                         season=season, 
                         episode=episode, 
                         download_url=download_url,
                         time_position=time_position,
                         is_favorite=is_favorite)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.args.get('password', '')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin1234')  # Fallback to default for development

        if password == admin_password:
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error="Invalid password")

    return render_template('admin_login.html')

@app.route('/admin')
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    return render_template('admin.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/admin/add_anime', methods=['POST'])
def add_anime():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    # Get form data
    title = request.form.get('title')
    description = request.form.get('description')
    image = request.form.get('image')
    genres = [g.strip().lower() for g in request.form.get('genres', '').split(',')]
    rating = float(request.form.get('rating', 0))
    featured = request.form.get('featured') == 'yes'
    episode_count = int(request.form.get('episode_count', 1))

    # Load existing anime data
    anime_data = load_anime_data()

    # Generate a new ID (max + 1)
    new_id = 1
    if anime_data:
        new_id = max(a.get('id', 0) for a in anime_data) + 1

    # Create episodes list
    episodes = []
    for i in range(1, episode_count + 1):
        episodes.append({
            'episode_number': i,
            'title': request.form.get(f'episode_title_{i}'),
            'description': request.form.get(f'episode_description_{i}'),
            'video_url': request.form.get(f'episode_video_{i}')
        })

    # Create the new anime object
    new_anime = {
        'id': new_id,
        'title': title,
        'description': description,
        'image': image,
        'genres': genres,
        'rating': rating,
        'featured': featured,
        'seasons': [
            {
                'season_number': 1,
                'episodes': episodes
            }
        ]
    }

    # Add to the anime data and save
    anime_data.append(new_anime)
    success = save_anime_data(anime_data)

    if success:
        return render_template('admin.html', message="Anime added successfully!", success=True)
    else:
        return render_template('admin.html', message="Error adding anime. Please try again.", success=False)

@app.route('/categories')
@login_required
def categories():
    anime_data = load_anime_data()
    genres = get_all_genres()

    # Create dictionary of genres and their anime
    genres_dict = {genre: [] for genre in genres}

    for anime in anime_data:
        for genre in anime.get('genres', []):
            if genre.lower() in genres_dict:
                genres_dict[genre.lower()].append(anime)

    return render_template('categories.html', all_anime=anime_data, genres=genres, genres_dict=genres_dict)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si l'utilisateur est déjà connecté, rediriger vers l'accueil
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    # Traitement du formulaire de connexion
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Vérification des identifiants
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # Mettre à jour la date de dernière connexion
            user.last_login = datetime.datetime.utcnow()
            db.session.commit()

            # Connecter l'utilisateur
            login_user(user)
            logger.debug(f"User {username} logged in successfully")

            # Redirection vers la page demandée ou l'accueil
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('index'))
        else:
            logger.debug(f"Failed login attempt for user {username}")
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'danger')

    return render_template('login_new.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Si l'utilisateur est déjà connecté, rediriger vers l'accueil
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    # Traitement du formulaire d'inscription
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Vérifier si les mots de passe correspondent
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return render_template('register_new.html')

        # Vérifier si le nom d'utilisateur existe déjà
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash('Ce nom d\'utilisateur est déjà pris.', 'danger')
        else:
            # Créer un nouvel utilisateur
            new_user = User(username=username)
            new_user.set_password(password)

            # Enregistrer en base de données
            db.session.add(new_user)
            db.session.commit()

            logger.debug(f"New user registered: {username}")
            flash('Votre compte a été créé avec succès! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('login'))

    return render_template('register_new.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # Récupérer les données du formulaire
        current_password = request.form.get('current_password')
        new_username = request.form.get('new_username')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Vérifier le mot de passe actuel
        if not current_user.check_password(current_password):
            flash('Mot de passe actuel incorrect', 'danger')
            return redirect(url_for('settings'))

        # Mettre à jour le nom d'utilisateur si fourni
        if new_username and new_username != current_user.username:
            # Vérifier si le nom d'utilisateur existe déjà
            if User.query.filter_by(username=new_username).first():
                flash('Ce nom d\'utilisateur est déjà pris', 'danger')
                return redirect(url_for('settings'))
            current_user.username = new_username

        # Mettre à jour le mot de passe si fourni
        if new_password:
            if new_password != confirm_password:
                flash('Les nouveaux mots de passe ne correspondent pas', 'danger')
                return redirect(url_for('settings'))
            current_user.set_password(new_password)

        # Sauvegarder les modifications
        db.session.commit()
        flash('Paramètres mis à jour avec succès', 'success')
        return redirect(url_for('settings'))

    return render_template('settings.html')

@app.route('/profile')
@login_required
def profile():
    # Récupérer les animes en cours de visionnage
    progress_data = UserProgress.query.filter_by(user_id=current_user.id).order_by(UserProgress.last_watched.desc()).all()

    # Récupérer les détails des animes
    anime_data = load_anime_data()
    watching_anime = []

    for progress in progress_data:
        anime = next((a for a in anime_data if int(a.get('id', 0)) == progress.anime_id), None)
        if anime:
            # Trouver la saison et l'épisode
            season = next((s for s in anime.get('seasons', []) if s.get('season_number') == progress.season_number), None)
            episode = None
            if season:
                episode = next((e for e in season.get('episodes', []) if e.get('episode_number') == progress.episode_number), None)

            watching_anime.append({
                'progress': progress,
                'anime': anime,
                'season': season,
                'episode': episode
            })

    # Récupérer les favoris
    favorites = UserFavorite.query.filter_by(user_id=current_user.id).all()
    favorite_anime = []

    for favorite in favorites:
        anime = next((a for a in anime_data if int(a.get('id', 0)) == favorite.anime_id), None)
        if anime:
            favorite_anime.append(anime)

    return render_template('profile_new.html', 
                          watching_anime=watching_anime, 
                          favorite_anime=favorite_anime)

@app.route('/remove-from-watching', methods=['POST'])
@login_required
def remove_from_watching():
    try:
        if request.method == 'POST':
            anime_id = request.form.get('anime_id', type=int)
            if anime_id:
                # Supprimer toutes les entrées de progression pour cet anime
                UserProgress.query.filter_by(
                    user_id=current_user.id,
                    anime_id=anime_id
                ).delete()
                
                db.session.commit()
                return jsonify({'success': True})
            
        return jsonify({'success': False, 'error': 'ID anime manquant'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/save-progress', methods=['POST'])
@login_required
def save_progress():
    if request.method == 'POST':
        anime_id = request.form.get('anime_id', type=int)
        season_number = request.form.get('season_number', type=int)
        episode_number = request.form.get('episode_number', type=int)
        time_position = request.form.get('time_position', type=float)
        completed = request.form.get('completed') == 'true'

        # Chercher une entrée existante
        progress = UserProgress.query.filter_by(
            user_id=current_user.id,
            anime_id=anime_id,
            season_number=season_number,
            episode_number=episode_number
        ).first()

        if progress:
            # Mettre à jour l'entrée existante
            progress.time_position = time_position
            progress.completed = completed
            progress.last_watched = datetime.datetime.utcnow()
        else:
            # Créer une nouvelle entrée
            progress = UserProgress(
                user_id=current_user.id,
                anime_id=anime_id,
                season_number=season_number,
                episode_number=episode_number,
                time_position=time_position,
                completed=completed,
                last_watched=datetime.datetime.utcnow()
            )
            db.session.add(progress)

        if progress:
            # Mettre à jour l'entrée existante, mais conserver le statut "terminé" si déjà marqué
            if not progress.completed:  # Si l'épisode n'était pas déjà terminé
                progress.time_position = time_position
                progress.completed = completed
            else:
                # Si l'épisode était déjà marqué comme terminé, ne le remettre "en cours" que si explicitement demandé
                if not completed:
                    # On ne remet pas à "non terminé" un épisode déjà marqué terminé
                    # sauf si le temps est revenu en arrière (par ex. début de l'épisode)
                    if time_position < progress.time_position * 0.5:  # Si position actuelle < 50% de la position sauvegardée
                        progress.completed = False
                        progress.time_position = time_position

            # Toujours mettre à jour la date de dernière visualisation
            progress.last_watched = datetime.datetime.utcnow()
        else:
            # Créer une nouvelle entrée
            progress = UserProgress(
                user_id=current_user.id,
                anime_id=anime_id,
                season_number=season_number,
                episode_number=episode_number,
                time_position=time_position,
                completed=completed
            )
            db.session.add(progress)

        db.session.commit()
        return {'success': True}, 200

    return {'success': False, 'error': 'Invalid request'}, 400

@app.route('/toggle-favorite', methods=['POST'])
@login_required
def toggle_favorite():
    if request.method == 'POST':
        anime_id = request.form.get('anime_id', type=int)

        # Vérifier si l'anime est déjà dans les favoris
        favorite = UserFavorite.query.filter_by(
            user_id=current_user.id, 
            anime_id=anime_id
        ).first()

        if favorite:
            # Supprimer des favoris
            db.session.delete(favorite)
            db.session.commit()
            return {'success': True, 'action': 'removed'}, 200
        else:
            # Ajouter aux favoris
            favorite = UserFavorite(
                user_id=current_user.id,
                anime_id=anime_id
            )
            db.session.add(favorite)
            db.session.commit()
            return {'success': True, 'action': 'added'}, 200

    return {'success': False, 'error': 'Invalid request'}, 400
@app.route('/documentation')
@login_required
def documentation():
    return render_template('documentation.html')

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    # Choisir le template en fonction de l'authentification
    if current_user.is_authenticated:
        return render_template('404.html'), 404
    else:
        return render_template('404_public.html'), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    # Choisir le template en fonction de l'authentification
    if current_user.is_authenticated:
        return render_template('404.html'), 500
    else:
        return render_template('404_public.html'), 500

# Créer les tables au démarrage
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)