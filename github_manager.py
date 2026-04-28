from github import Github, GithubException
import os
from dotenv import load_dotenv
import datetime
import re
from readme_builder import build_readme

load_dotenv()

class GitHubManager:
    """
    Manages GitHub repository operations
    Future-proof: Can use user's token or default token
    """
    
    def __init__(self, token=None):
        """
        Initialize GitHub manager
        token: Optional user's GitHub token. If None, uses default from .env
        """
        raw_token = token or os.getenv('GITHUB_TOKEN')
        if raw_token:
            raw_token = str(raw_token).strip().replace('\r', '').replace('\n', '')
            if raw_token.lower().startswith('bearer '):
                raw_token = raw_token[7:].strip()

        self.token = raw_token
        if not self.token:
            raise ValueError("No GitHub token provided")
        
        self.github = Github(self.token, timeout=30)
        self.user = self.github.get_user()
    
    def generate_repo_name(self, description, company_name=None):
        """
        Generate a unique, valid GitHub repository name.

        Priority:
          1. company_name (e.g. "Gym Max" → gym-max-20260428-170539)
          2. First 3 words of description as fallback
        """
        # Prefer the company name when provided
        source = (company_name or '').strip() or description
        clean = source.lower()
        # Remove special characters, keep only alphanumeric and spaces
        clean = re.sub(r'[^a-z0-9\s]', '', clean)
        words = clean.split()[:4]
        base_name = '-'.join(words) if words else 'ai-website'

        # Add timestamp for uniqueness
        timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        repo_name = f"{base_name}-{timestamp}"

        # GitHub repo names must be <= 100 characters
        if len(repo_name) > 100:
            repo_name = repo_name[:100]

        return repo_name
    
    def create_repository(self, repo_name, description="AI Generated Website", private=False):
        """
        Create a new GitHub repository, retrying with a counter suffix if the
        name is already taken.  Avoids the old recursive-timestamp approach that
        could produce absurdly long names and 403 errors.

        Args:
            repo_name: Name of the repository
            description: Repository description
            private: Whether repo should be private (default: False)

        Returns:
            GitHub repository object
        """
        max_attempts = 5
        # Keep the base name short enough so suffixes always fit within 100 chars.
        base_name = repo_name[:90]
        candidate = base_name

        for attempt in range(1, max_attempts + 1):
            try:
                print(f"Creating GitHub repository: {candidate}")
                repo = self.user.create_repo(
                    name=candidate,
                    description=description,
                    private=private,
                    auto_init=False,
                )
                print(f"✓ Repository created: {repo.html_url}")
                return repo

            except GithubException as e:
                if e.status == 422 and attempt < max_attempts:
                    # Name already taken — append a short counter suffix.
                    candidate = f"{base_name}-{attempt + 1}"
                    print(f"Repository exists, trying: {candidate}")
                    continue

                raise Exception(
                    f"Failed to create repository (HTTP {e.status} on "
                    f"attempt {attempt}/{max_attempts}): {e.data}"
                )
    
    def _create_or_update_file(self, repo, path, message, content):
        """
        Create a file or update it if it already exists (fetches sha automatically).
        """
        try:
            existing = repo.get_contents(path)
            repo.update_file(
                path=path,
                message=message,
                content=content,
                sha=existing.sha
            )
        except GithubException as e:
            if e.status == 404:
                repo.create_file(
                    path=path,
                    message=message,
                    content=content
                )
            else:
                raise

    def push_files(self, repo, files, description="", branding=None, structure_info=None):
        """
        Push multiple files to the repository.

        Args:
            repo          : GitHub repository object
            files         : Dictionary of {filename: content}
            description   : Original user description (used in README)
            branding      : Branding dict (company_name, tagline, colors)
            structure_info: Structure dict returned by determine_website_structure()

        Returns:
            Repository URL
        """
        try:
            print(f"Pushing {len(files)} files to repository...")

            # Build a rich README using the dedicated builder
            readme_content = build_readme(
                description=description,
                branding=branding or {},
                structure_info=structure_info or {},
                files=files,
            )

            # Push README first
            self._create_or_update_file(
                repo=repo,
                path="README.md",
                message="Initial commit: Add README",
                content=readme_content
            )
            print("✓ README.md created")
            
            # Push all generated files
            for filename, content in files.items():
                self._create_or_update_file(
                    repo=repo,
                    path=filename,
                    message=f"Add {filename}",
                    content=content
                )
                print(f"✓ {filename} pushed")
            
            print(f"✓ All files pushed successfully!")
            return repo.html_url
            
        except Exception as e:
            raise Exception(f"Failed to push files: {str(e)}")
    
    def create_and_push(self, description, files, branding=None, structure_info=None):
        """
        Complete workflow: Create repo and push files.

        Args:
            description   : Project description (for repo name and description)
            files         : Dictionary of {filename: content}
            branding      : Branding dict (company_name, tagline, colors)
            structure_info: Structure dict returned by determine_website_structure()

        Returns:
            Dictionary with repo_name, repo_url, and success status
        """
        try:
            # Generate unique repo name
            company = (branding or {}).get('company_name', '')
            repo_name = self.generate_repo_name(description, company_name=company)

            # Create repository
            repo = self.create_repository(
                repo_name=repo_name,
                description=f"AI Generated: {description}"
            )

            # Push files with rich README
            repo_url = self.push_files(
                repo,
                files,
                description=description,
                branding=branding,
                structure_info=structure_info,
            )
            
            return {
                'success': True,
                'repo_name': repo_name,
                'repo_url': repo_url,
                'username': self.user.login
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }