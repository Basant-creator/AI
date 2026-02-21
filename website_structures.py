"""
Website structure templates for different types of websites
Defines file structures for various website types
"""

def get_landing_page_structure():
    """Single page website - simple and fast"""
    return {
        'files': [
            'index.html',
            'style.css',
            'script.js'
        ],
        'description': 'Single-page landing site'
    }

def get_multi_page_structure():
    """Multi-page website with navigation"""
    return {
        'files': [
            'index.html',
            'about.html',
            'services.html',
            'contact.html',
            'css/style.css',
            'css/responsive.css',
            'js/script.js',
            'js/navigation.js'
        ],
        'description': 'Multi-page website with navigation'
    }

def get_portfolio_structure():
    """Portfolio website for showcasing work"""
    return {
        'files': [
            'index.html',
            'about.html',
            'projects.html',
            'project-detail.html',
            'contact.html',
            'css/style.css',
            'css/projects.css',
            'js/script.js',
            'js/projects.js',
            'js/filter.js'
        ],
        'description': 'Portfolio website with project showcase'
    }

def get_blog_structure():
    """Blog website with articles"""
    return {
        'files': [
            'index.html',
            'article.html',
            'about.html',
            'contact.html',
            'css/style.css',
            'css/blog.css',
            'js/script.js',
            'js/blog.js'
        ],
        'description': 'Blog website with article pages'
    }

def get_webapp_structure():
    """Web application with authentication (frontend + backend, Render-deployable)"""
    return {
        'files': [
            # Frontend - all served as static from public/
            'public/index.html',
            'public/login.html',
            'public/signup.html',
            'public/dashboard.html',
            'public/css/style.css',
            'public/css/auth.css',
            'public/css/dashboard.css',
            'public/js/main.js',
            'public/js/auth.js',
            'public/js/dashboard.js',

            # Backend
            'backend/server.js',
            'backend/routes/auth.js',
            'backend/routes/users.js',
            'backend/models/User.js',
            'backend/middleware/auth.js',
            'backend/config/db.js',

            # Config / deployment
            'package.json',
            '.env.example',
            '.gitignore',
            'README.md',
        ],
        'description': 'Production-ready full-stack web application with authentication (Render-deployable)'
    }

def get_ecommerce_structure():
    """E-commerce website with products and cart"""
    return {
        'files': [
            # Frontend
            'index.html',
            'products.html',
            'product-detail.html',
            'cart.html',
            'checkout.html',
            'login.html',
            'signup.html',
            'account.html',
            'css/style.css',
            'css/products.css',
            'css/cart.css',
            'js/products.js',
            'js/cart.js',
            'js/checkout.js',
            
            # Backend
            'backend/server.js',
            'backend/routes/products.js',
            'backend/routes/cart.js',
            'backend/routes/orders.js',
            'backend/models/Product.js',
            'backend/models/Order.js',
            'backend/models/User.js',
            
            # Config
            'package.json',
            'README.md',
            'database/schema.sql'
        ],
        'description': 'E-commerce website with shopping cart'
    }

def determine_website_structure(description):
    """
    Intelligently determine website structure based on description
    Returns structure info with file list and metadata
    """
    description_lower = description.lower()
    
    # Detection keywords
    has_auth = any(word in description_lower for word in [
        'login', 'signup', 'authentication', 'user account', 
        'register', 'dashboard', 'profile', 'sign up', 'sign in'
    ])
    
    has_ecommerce = any(word in description_lower for word in [
        'shop', 'store', 'ecommerce', 'e-commerce', 'products', 
        'cart', 'buy', 'sell', 'checkout', 'payment'
    ])
    
    has_blog = any(word in description_lower for word in [
        'blog', 'articles', 'posts', 'cms', 'content management'
    ])
    
    has_portfolio = any(word in description_lower for word in [
        'portfolio', 'showcase', 'gallery', 'projects', 'work'
    ])
    
    has_multipage = any(word in description_lower for word in [
        'pages', 'about page', 'contact page', 'multiple pages',
        'navigation', 'menu', 'services page'
    ])
    
    # Determine structure (priority order)
    if has_ecommerce:
        structure = get_ecommerce_structure()
        return {
            'type': 'ecommerce',
            'files': structure['files'],
            'description': structure['description'],
            'needs_backend': True,
            'needs_database': True,
            'backend_framework': 'express',
            'database_type': 'mongodb'
        }
    
    elif has_auth:
        structure = get_webapp_structure()
        return {
            'type': 'web_application',
            'files': structure['files'],
            'description': structure['description'],
            'needs_backend': True,
            'needs_database': True,
            'backend_framework': 'express',
            'database_type': 'mongodb'
        }
    
    elif has_blog:
        structure = get_blog_structure()
        return {
            'type': 'blog',
            'files': structure['files'],
            'description': structure['description'],
            'needs_backend': False,
            'needs_database': False
        }
    
    elif has_portfolio:
        structure = get_portfolio_structure()
        return {
            'type': 'portfolio',
            'files': structure['files'],
            'description': structure['description'],
            'needs_backend': False,
            'needs_database': False
        }
    
    elif has_multipage:
        structure = get_multi_page_structure()
        return {
            'type': 'multi_page',
            'files': structure['files'],
            'description': structure['description'],
            'needs_backend': False,
            'needs_database': False
        }
    
    else:
        structure = get_landing_page_structure()
        return {
            'type': 'landing_page',
            'files': structure['files'],
            'description': structure['description'],
            'needs_backend': False,
            'needs_database': False
        }