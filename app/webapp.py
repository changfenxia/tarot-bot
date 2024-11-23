import os
from aiohttp import web
from jinja2 import Environment, FileSystemLoader

# Initialize Jinja2
env = Environment(loader=FileSystemLoader('app/templates'))

async def tarot_page(request):
    """Render tarot question page"""
    template = env.get_template('tarot.html')
    return web.Response(
        text=template.render(),
        content_type='text/html'
    )

async def init_app():
    """Initialize web application"""
    app = web.Application()
    app.router.add_get('/tarot', tarot_page)
    app.router.add_static('/static', 'app/static')
    return app

if __name__ == '__main__':
    app = init_app()
    web.run_app(app, host='0.0.0.0', port=int(os.getenv('PORT', 8080)))
