import os
import markdown
import frontmatter
import json
from jinja2 import Environment, FileSystemLoader

class SSG:
    def __init__(self, templates_dir='src/generator/templates', content_dir='src/generator/content', output_dir='dist'):
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        self.env.filters['format_currency'] = self.format_currency
        self.content_dir = content_dir
        self.output_dir = output_dir
        self.data = self._load_data()

    def format_currency(self, value):
        try:
            return f"R$ {float(value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except (ValueError, TypeError):
            return value

    def _load_data(self):
        data = {}
        # Load courses.json
        courses_path = os.path.join(self.content_dir, 'cursos.json')
        if os.path.exists(courses_path):
            with open(courses_path, 'r', encoding='utf-8') as f:
                data['courses'] = json.load(f)
        return data

    def render_markdown(self, content):
        return markdown.markdown(content, extensions=['extra', 'toc', 'codehilite'])

    def build(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Process all markdown files in content directory
        for filename in os.listdir(self.content_dir):
            if filename.endswith('.md'):
                output_filename = filename.replace('.md', '.html')
                
                # Load frontmatter to check for custom template
                content_path = os.path.join(self.content_dir, filename)
                post = frontmatter.load(content_path)
                template_file = post.metadata.get('template', 'base.html')
                
                self.render_page(filename, template_file, output_filename)
        
        self.generate_seo_files()

    def generate_seo_files(self):
        pages = [f for f in os.listdir(self.output_dir) if f.endswith('.html')]
        base_url = "https://formarbem.org.br"
        
        # Sitemap.xml
        sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        for page in pages:
            sitemap_content += f'  <url>\n    <loc>{base_url}/{page}</loc>\n    <priority>0.8</priority>\n  </url>\n'
        sitemap_content += '</urlset>'
        
        with open(os.path.join(self.output_dir, 'sitemap.xml'), 'w', encoding='utf-8') as f:
            f.write(sitemap_content)
        
        # Robots.txt
        robots_content = f"User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml"
        with open(os.path.join(self.output_dir, 'robots.txt'), 'w', encoding='utf-8') as f:
            f.write(robots_content)
            
        print("Generated sitemap.xml and robots.txt")

    def render_page(self, content_file, template_file, output_file):
        content_path = os.path.join(self.content_dir, content_file)
        
        # Parse frontmatter and content
        post = frontmatter.load(content_path)
        html_content = self.render_markdown(post.content)
        
        # Prepare context for Jinja2
        context = post.metadata
        context['content'] = html_content
        context['site_data'] = self.data
        
        try:
            template = self.env.get_template(template_file)
            output = template.render(**context)

            with open(os.path.join(self.output_dir, output_file), 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Generated {output_file} using {template_file}")
        except Exception as e:
            print(f"Error rendering {content_file} with {template_file}: {e}")

if __name__ == "__main__":
    generator = SSG()
    generator.build()
