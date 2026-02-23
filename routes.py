import os
from flask import Flask,render_template,redirect,request,url_for
from datetime import datetime  
from flask_login import login_required,current_user,login_user,logout_user 
from models import UserModel,BlogModel,CategoryMaster,BlogComment,db,login 
from sqlalchemy import func
app = Flask(__name__) 
global_all_no = None 
global_all_category_name = None
app.secret_key = 'ItShouldBeLongEnough'
basedir = os.path.abspath(os.path.dirname(__file__)) 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir,'data.db') 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
db.init_app(app) 
login.init_app(app) 
login.login_view = 'login' 
@login.user_loader
def load_user(id):
    return UserModel.query.get(int(id))
def get_all_categories():
    global  global_all_no,global_all_category_name 
    all_category_info = db.session.query(CategoryMaster.category_id,CategoryMaster.category_name)
    all_category_info = list(all_category_info) 
    global_all_no,global_all_category_name = zip(*all_category_info)
@app.before_request 
def create_all():
    db.create_all() 
    get_all_categories() 
@app.route('/')
def home():
    return redirect(url_for('login'))   
@app.route('/register',methods=['POST','GET'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        if UserModel.query.filter_by(email=email).first():
            return "Email Already Exists" 
        user = UserModel(email=email,username=username)
        user.set_password(password) 
        db.session.add(user)
        db.session.commit() 
        return redirect(url_for('login'))
    return render_template('register.html')
@app.route('/login',methods=['POST','GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('blogs'))
    if request.method == 'POST':
        email = request.form.get('email')
        user = UserModel.query.filter_by(email=email).first() 
        if user is not None and user.check_password(request.form.get('password')): 
            login_user(user) 
            return redirect(url_for('blogs')) 
    return render_template('login.html')
@app.route('/logout')
def logout():
    logout_user() 
    return redirect('/login')     
@app.route('/blogs')
def blogs():
    if current_user.is_authenticated:
        return render_template('blogs_home.html')
    return redirect(url_for('listAllBlogs')) 
@app.route('/createBlog', methods=['GET', 'POST'])
@login_required 
def createBlog():
    if request.method == 'POST':
        # Print to your terminal to see if data is actually arriving
        print(f"Form Data: {request.form}") 
        
        category_id = request.form.get('category_id') 
        blog_text = request.form.get('blog_text')
        
        # Ensure we have data before saving
        if not category_id or not blog_text:
            return "Error: Missing Category or Blog Text"

        newBlog = BlogModel(
            category_id=int(category_id), # Cast to int for the Foreign Key
            blog_user_id=current_user.id,
            blog_text=blog_text,
            blog_creation_date=datetime.now(),
            blog_read_count=0,
            blog_rating_count=0 ) 
        db.session.add(newBlog)
        db.session.commit() 
        return redirect(url_for('blogs'))   
    
    return render_template('create_blog.html', 
                           all_category_id=global_all_no, 
                           all_category_name=global_all_category_name) 
@app.route('/viewBlog')
@login_required
def viewBlog():
    all_self_blogs = BlogModel.query.filter(BlogModel.blog_user_id == current_user.id).all() 
    return render_template('view_blog.html',all_self_blogs=all_self_blogs,all_categories=global_all_category_name)
     
@app.route('/self_blog_detail/<int:blog_model_id>/<string:blog_model_category>', methods=['GET', 'POST'])
@login_required 
def self_blog_detail(blog_model_id, blog_model_category):
    blog_model = BlogModel.query.get(blog_model_id)
    
    if not blog_model:
        return "Blog not found", 404
    
    if request.method == 'POST':
        if request.form['action'] == 'Update':
            blog_model.blog_text = request.form.get('blog_text')
            db.session.commit()
            return redirect(url_for('viewBlog'))
        elif request.form['action'] == 'Delete':
            db.session.delete(blog_model)
            db.session.commit()
            return redirect(url_for('viewBlog'))
    
   
    return render_template('self_blog_detail.html', 
                          blog_id=blog_model_id, 
                          blog_categories=blog_model_category, 
                          blog_text=blog_model.blog_text) 
@app.route('/listAllBlogs') 
def listAllBlogs():
    all_blogs = BlogModel.query.all() 
    all_users = UserModel.query.all()   
    return render_template('list_all_blogs.html',all_blogs=all_blogs,all_users=all_users,all_categories = global_all_category_name)       
from sqlalchemy import func

@app.route('/blogDetail/<int:blog_id>/<string:username>/<string:category>', methods=['GET','POST']) 
@login_required 
def blog_detail(blog_id, username, category):
    blog = BlogModel.query.get(blog_id)
    if request.method == 'GET':
        if current_user.id != blog.blog_user_id:
            blog.blog_read_count = blog.blog_read_count + 1 
            db.session.commit() 
        
        rating_data = db.session.query(func.avg(BlogComment.blog_rating)).filter(BlogComment.blog_id == blog_id).first()
        rating = rating_data[0] if rating_data else 0
        
        return render_template('blog_detail.html', blog=blog, rating=rating, author=username, category=category)
    else: 
        rate = request.form.get('rating') 
        comment = request.form.get('comment') 
        
        oldComment = BlogComment.query.filter(BlogComment.blog_id == blog_id).filter(BlogComment.comment_user_id == current_user.id).first() 
        today = datetime.now() 
        
        if oldComment == None:
            blog.blog_rating_count = blog.blog_rating_count + 1 
            newComment = BlogComment(
                blog_id = blog_id,
                comment_user_id = current_user.id, 
                blog_comment = comment, 
                blog_rating = rate, 
                blog_comment_date = today
            ) 
            db.session.add(newComment)      
        else: 
            oldComment.blog_comment = comment 
            oldComment.blog_rating = rate 
        db.session.commit() 
        return redirect(url_for('blogs'))
        
if __name__ == "__main__":
    app.run(debug=True)    
