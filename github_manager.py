from github import Github, GithubException
import time as _time
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
        
        self.github = Github(self.token, timeout=30, retry=0)
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

                if e.status == 403:
                    # Distinguish rate-limit from permission denied.
                    msg = str(e.data).lower()
                    if 'rate' in msg or 'abuse' in msg or 'secondary' in msg:
                        if attempt < max_attempts:
                            wait = min(15 * attempt, 60)
                            print(f"GitHub rate limit hit. Waiting {wait}s before retry {attempt + 1}...")
                            _time.sleep(wait)
                            continue
                        raise Exception(
                            'GitHub rate limit exceeded after multiple retries. '
                            'Wait a few minutes and try again.'
                        )
                    raise Exception(
                        'GitHub returned 403 Forbidden. Your token may lack '
                        'the "repo" scope needed to create repositories. '
                        'Generate a new token with full repo permissions.'
                    )

                raise Exception(
                    f"Failed to create repository (HTTP {e.status} on "
                    f"attempt {attempt}/{max_attempts}): {e.data}"
                )
    
    def _push_files_via_tree(self, repo, all_files):
        """
        Push every file in a single commit using the low-level Git Data API.

        Steps (3 API calls total, regardless of file count):
          1. Create a git tree with all file blobs
          2. Create a commit pointing to that tree
          3. Update refs/heads/main to that commit
        """
        tree_items = []
        for path, content in all_files.items():
            # InputGitTreeElement: mode 100644 = regular file, type blob
            tree_items.append({
                'path': path,
                'mode': '100644',
                'type': 'blob',
                'content': content,
            })

        # 1. Create the tree (no base_tree → brand-new root)
        git_tree = repo.create_git_tree(
            [repo.create_git_tree_element(**item) for item in tree_items]
        )

        # 2. Create the commit
        commit = repo.create_git_commit(
            message='Initial commit: AI-generated website',
            tree=git_tree,
            parents=[],
        )

        # 3. Point main branch at the new commit
        #    New repos may not have any ref yet, so create it if needed.
        try:
            ref = repo.get_git_ref('heads/main')
            ref.edit(sha=commit.sha, force=True)
        except GithubException:
            repo.create_git_ref(ref=f'refs/heads/main', sha=commit.sha)

        return repo.html_url

    def push_files(self, repo, files, description="", branding=None, structure_info=None):
        """
        Push multiple files to the repository in a single atomic commit.

        Uses the Git Trees API so that ALL files (including the README) land
        in one commit with only ~3 GitHub API calls — avoiding the secondary
        rate limit that the old file-by-file approach triggered.

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
            total = len(files) + 1  # +1 for README
            print(f"Pushing {total} files to repository (single commit)...")

            # Build a rich README using the dedicated builder
            readme_content = build_readme(
                description=description,
                branding=branding or {},
                structure_info=structure_info or {},
                files=files,
            )

            # Combine README + generated files
            all_files = {'README.md': readme_content}
            all_files.update(files)

            # Retry with backoff if the push fails (transient rate-limit, etc.)
            max_push_retries = 3
            last_push_error = None

            for push_attempt in range(1, max_push_retries + 1):
                try:
                    repo_url = self._push_files_via_tree(repo, all_files)
                    print(f"✓ All {total} files pushed in one commit!")
                    return repo_url
                except Exception as push_err:
                    last_push_error = push_err
                    if push_attempt < max_push_retries:
                        wait = 15 * push_attempt  # 15s, 30s
                        print(f"Push failed (attempt {push_attempt}/{max_push_retries}): {push_err}")
                        print(f"Retrying in {wait}s...")
                        _time.sleep(wait)
                    else:
                        print(f"Push failed after {max_push_retries} attempts.")

            raise last_push_error

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