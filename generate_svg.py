import os
import re
from xml.sax.saxutils import escape
import requests
import base64

# ===== CONFIGURATION =====
INPUT_FILE = "ascii-art.txt"
OUTPUT_FILE = "profile.svg"
FONT_SIZE = 18
TEXT_COLOR = "#3A7DD1"
BACKGROUND_COLOR = "#0D1117"
PADDING = 20
FONT_FAMILY = "'Courier New', monospace"

# Right panel settings
ABOUT_TEXT_COLOR = "#58A6FF"
YELLOW_COLOR = "#FCEE0A"
DOT_COLOR = "#30363D"
SECTION_SPACING = 30
LINE_HEIGHT = 28

USERNAME = "Abheelash-Mishra"
TOKEN = os.getenv("GH_KEY")

CONTENT = {
    "HEY EVERYONE!": {
        "Name": "Abheelash Mishra",
        "Occupation": "Software Engineer - Baton Systems",
        "Passion": "To Learn, Explore, and Solve",
    },
    "My Technical Stuff": {
        "Languages": "Python, Java, JavaScript, SQL, C, C++",
        "Frontend": "JavaScript, React.js, Next.js",
        "Backend": "Node.js, Express.js, Spring Boot",
        "Dev Tools": "Git, Docker",
        "Databases": "MySQL, PostgreSQL, MongoDB, H2",
        "Cloud Platforms": "AWS, Oracle Cloud, Google Cloud",
    },
    "GitHub Stats": {
        "Repositories": "N/A",
        "Commits": "N/A",
        "LOC Count": "N/A",
        "Profile Views": "N/A"
    },
}

def get_commit_count(username, repo_name, headers):
    total_commits = 0
    end_cursor = None

    query = '''
    query($owner: String!, $repo: String!, $endCursor: String) {
      repository(owner: $owner, name: $repo) {
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 100, after: $endCursor) {
                totalCount
                pageInfo {
                  endCursor
                  hasNextPage
                }
              }
            }
          }
        }
      }
    }'''

    while True:
        variables = {
            'owner': username,
            'repo': repo_name,
            'endCursor': end_cursor
        }

        url = 'https://api.github.com/graphql'
        response = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)

        if response.status_code == 200:
            data = response.json()

            commits_page = data['data']['repository']['defaultBranchRef']['target']['history']
            total_commits += commits_page['totalCount']

            if commits_page['pageInfo']['hasNextPage']:
                end_cursor = commits_page['pageInfo']['endCursor']
            else:
                break
        else:
            print(f"Error Code: {response.status_code} || {response.text}")
            break

    return total_commits


def fetch_github_stats_with_loc(username, token=None):
    headers = {"Authorization": f"token {token}"} if token else {}

    user_url = f"https://api.github.com/users/{username}"
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&type=owner"

    user_resp = requests.get(user_url, headers=headers)
    repos_resp = requests.get(repos_url, headers=headers)

    if user_resp.status_code != 200 or repos_resp.status_code != 200:
        raise Exception("GitHub API error")

    user_data = user_resp.json()
    repos_data = repos_resp.json()

    total_repos = user_data.get("public_repos", 0)
    total_commits = 0
    total_loc = 0

    repo_num = 1

    for repo in repos_data:
        if repo.get("fork"):
            continue

        print("Repo Number: ", repo_num)
        repo_num += 1

        repo_name = repo["name"]
        default_branch = repo.get("default_branch", "main")

        # Count commits using pagination
        total_commits += get_commit_count(username, repo_name, headers)

        # Fetch tree to count LOC
        tree_url = f"https://api.github.com/repos/{username}/{repo_name}/git/trees/{default_branch}?recursive=1"
        tree_resp = requests.get(tree_url, headers=headers)
        if tree_resp.status_code != 200:
            continue

        tree = tree_resp.json().get("tree", [])

        for obj in tree:
            if obj["type"] != "blob":
                continue

            path = obj["path"]
            if any(path.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".exe", ".pdf", ".mp4", ".zip", ".tar", ".ico", ".json", ".svg", ".txt"]):
                continue

            blob_url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{path}"
            blob_resp = requests.get(blob_url, headers=headers)
            if blob_resp.status_code != 200:
                continue

            blob = blob_resp.json()
            content = blob.get("content")
            encoding = blob.get("encoding")

            if not content or encoding != "base64":
                continue

            try:
                decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
                loc = len(decoded.strip().splitlines())
                total_loc += loc
            except Exception:
                continue

    return {
        "repos": total_repos,
        "commits": total_commits,
        "loc": total_loc,
    }

def create_split_svg():
    try:
        # Read ASCII art
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            ascii_art = [line.rstrip('\n') for line in f]

        # Calculate dimensions
        max_ascii_width = max(len(line) for line in ascii_art)
        char_width = FONT_SIZE * 0.6
        ascii_panel_width = max_ascii_width * char_width + PADDING * 2
        total_width = ascii_panel_width * 2
        right_panel_width = ascii_panel_width

        # Calculate content height
        total_lines = sum(len(section) + 1 for section in CONTENT.values())  # +1 for section headers
        content_height = total_lines * LINE_HEIGHT + (len(CONTENT) - 1) * SECTION_SPACING
        start_y = (700 - content_height) / 2  # Centered in 700px height

        # Create SVG
        svg_content = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
            <svg width="{total_width}" height="700" viewBox="0 0 {total_width} 700"
                 xmlns="http://www.w3.org/2000/svg">
              <rect width="100%" height="100%" fill="{BACKGROUND_COLOR}"/>
              
              <!-- Left Panel - ASCII Art -->
              <g font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}" 
                 fill="{TEXT_COLOR}" xml:space="preserve">
            '''

        # Add ASCII Art
        y_pos = (700 - len(ascii_art)*FONT_SIZE)/2 + FONT_SIZE
        for line in ascii_art:
            preserved_line = escape(line).replace(' ', '&#160;')
            svg_content += f'    <text x="{PADDING}" y="{y_pos}">{preserved_line}</text>\n'
            y_pos += FONT_SIZE

        svg_content += f'''  </g>
          <line x1="{ascii_panel_width - 10}" y1="20" x2="{ascii_panel_width - 10}" y2="680" stroke="{YELLOW_COLOR}" stroke-width="2"/>
          <line x1="{ascii_panel_width - 4}" y1="20" x2="{ascii_panel_width - 4}" y2="680" stroke="{YELLOW_COLOR}" stroke-width="2"/>
  
          <!-- Right Panel - Technical Profile -->
          <g transform="translate({ascii_panel_width}, 0)">
            <rect width="{right_panel_width}" height="100%" fill="{BACKGROUND_COLOR}"/>
            <g font-family="'Fira Code', monospace" font-size="15">
        '''

        current_y = start_y
        for section, items in CONTENT.items():
            # Section header
            svg_content += f'''
                <text x="{right_panel_width / 2}" y="{current_y + 8}" 
                    font-size="20" font-weight="800" fill="{YELLOW_COLOR}" 
                    text-anchor="middle">{section.upper()}</text>
            '''

            current_y += LINE_HEIGHT + 10

            if section == "GitHub Stats":
                item_list = list(items.items())
                for i in range(0, len(item_list), 2):
                    col1 = item_list[i]
                    col2 = item_list[i+1] if i+1 < len(item_list) else ("", "")

                    # Column widths
                    col1_x = 50
                    col2_x = right_panel_width // 2 + 20
                    max_col_width = right_panel_width // 2 - 70  # Leave space for dots and value

                    for col_x, (label, value) in zip([col1_x, col2_x], [col1, col2]):
                        if not label:
                            continue
                        label_width = len(label) * 8
                        value_width = len(value) * 7
                        dots_width = max_col_width - label_width - value_width
                        dot_count = max(int(dots_width // 8), 0)

                        svg_content += f'''
                            <text x="{col_x}" y="{current_y}" font-size="18" font-weight="600" fill="{YELLOW_COLOR}">{label}</text>
                            <text x="{col_x + label_width}" y="{current_y}" fill="{DOT_COLOR}">{'.' * dot_count}</text>
                            <text x="{col_x + label_width + dot_count * 8 + 5}" y="{current_y}" font-size="18" fill="{ABOUT_TEXT_COLOR}">{value}</text>
                        '''
                    current_y += LINE_HEIGHT

            else:
                # Section items for non-GitHub Stats sections
                for label, value in items.items():
                    label_width = len(label) * 8.5
                    dots_width = (right_panel_width - 100 - label_width - len(value)*7.5)
                    dot_count = int(dots_width // 9) - 3

                    svg_content += f'''
                        <text x="50" y="{current_y}" font-size="18" font-weight="600" fill="{YELLOW_COLOR}">{label}</text>
                        <text x="{50 + label_width}" y="{current_y}" fill="{DOT_COLOR}">{"." * dot_count}</text>
                        <text x="{right_panel_width - 50}" y="{current_y}" font-size="18" fill="{ABOUT_TEXT_COLOR}" text-anchor="end">{value}</text>
                    '''
                    current_y += LINE_HEIGHT

            current_y += SECTION_SPACING - LINE_HEIGHT + 30

        svg_content += '''
                </g>
              </g>
            </svg>'''

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        print(f"SVG generated: {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error: {str(e)}")


def fetch_profile_views(username):
    try:
        url = f"https://komarev.com/ghpvc/?username={username}&style=for-the-badge"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("Failed to fetch profile views")

        match = re.search(r"<title>PROFILE VIEWS: (\d+)</title>", response.text)
        if match:
            return int(match.group(1))
        else:
            raise Exception("View count not found in response")
    except Exception as e:
        print(f"Error fetching profile views: {e}")
        return 0


if __name__ == '__main__':
    views = fetch_profile_views(USERNAME)
    if views:
        CONTENT["GitHub Stats"]["Profile Views"] = str(views)

    stats = fetch_github_stats_with_loc(USERNAME, TOKEN)
    CONTENT["GitHub Stats"]["Repositories"] = str(stats["repos"])
    CONTENT["GitHub Stats"]["Commits"] = str(stats["commits"])
    CONTENT["GitHub Stats"]["LOC Count"] = str(stats["loc"])

    create_split_svg()

