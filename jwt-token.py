import json, os, sys, asyncio, subprocess

# --- Auto Install Missing Modules ---
def install_and_import(package, import_name=None):
    try:
        __import__(import_name or package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])
        __import__(import_name or package)

install_and_import("aiohttp")
install_and_import("rich")
install_and_import("pyfiglet")

import aiohttp
from pyfiglet import figlet_format
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule

os.system("clear")
console = Console()

# --- Logo ---
def print_logo():
    try:
        title = figlet_format("JWT", font="slant")  
    except Exception:
        title = figlet_format("JWT")  

    console.print(Panel.fit(
        f"[bold cyan]{title}[/]\n[white]Owner:[/][bold magenta] Altalimul Islam[/]",
        border_style="bright_blue",
        subtitle="Fast • Async • Beautiful",
        subtitle_align="right"
    ))
    console.print(Rule(style="bright_blue"))

# --- Fetch Function ---
async def fetch_token(session, uid, password, idx, total):
    url = f"https://jwt-token-generator.axmhere.xyz/jwt-token?uid={uid}&password={password}"
    
    # Fetching message
    console.print(Panel.fit(
        f"[bold white][{idx}/{total}][/bold white] 🔄 Fetching token for UID: [bold yellow]{uid}[/]",
        style="cyan"
    ))

    try:
        async with session.get(url, timeout=15) as resp:
            if resp.status == 200:
                data = await resp.json()
                token = data.get("token")
                if token:
                    console.print(Panel.fit(
                        f"[bold white][{idx}/{total}][/bold white] ✅ Token fetched for UID: [bold green]{uid}[/]",
                        style="green"
                    ))
                    return token
    except Exception as e:
        console.print(Panel.fit(
            f"[bold white][{idx}/{total}][/bold white] ❌ Error fetching UID {uid}: {e}",
            style="red"
        ))
        return None

    console.print(Panel.fit(
        f"[bold white][{idx}/{total}][/bold white] ❌ Failed to fetch token for UID: [bold red]{uid}[/]",
        style="red"
    ))
    return None

# --- Main Processor ---
async def process_credentials(json_file, output_file):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            credentials = json.load(f)
    except Exception as e:
        console.print(Panel.fit(f"❌ Failed to load credentials: {e}", style="bold red"))
        return

    valid = [(i, c.get("uid"), c.get("password"))
             for i, c in enumerate(credentials, start=1)
             if c.get("uid") and c.get("password")]

    total = len(valid)
    console.print(Panel.fit(
        f"📄 Loaded [bold cyan]{total}[/] credential(s) from [yellow]{json_file}[/]\n"
        f"💾 Output: [green]{output_file}[/]",
        style="cyan"
    ))

    if total == 0:
        console.print(Panel.fit("⚠️ No valid credentials found (need uid & password).", style="bold yellow"))
        return

    tokens = []
    failures = 0

    timeout = aiohttp.ClientTimeout(total=None, connect=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for idx, uid, pwd in valid:
            token = await fetch_token(session, uid, pwd, idx, total)
            if token:
                tokens.append({"token": token})
            else:
                failures += 1

    # Save file
    if tokens:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tokens, f, indent=2, ensure_ascii=False)

    # Summary table
    summary = Table(title="🎯 Token Fetch Summary", show_lines=True, header_style="bold cyan")
    summary.add_column("Total", justify="center")
    summary.add_column("Success", justify="center")
    summary.add_column("Failed", justify="center")
    summary.add_column("Saved File", justify="center", overflow="fold")
    summary.add_row(str(total), str(len(tokens)), str(failures), output_file if tokens else "—")
    console.print(summary)

    if not tokens:
        console.print(Panel.fit("⚠️ No tokens were fetched.", style="bold yellow"))

# --- Output path ---
def derive_output_path(input_path: str) -> str:
    folder = os.path.dirname(input_path)
    filename = os.path.basename(input_path)
    name, _ = os.path.splitext(filename)
    return os.path.join(folder, f"{name}_token.json")

# --- Run ---
if __name__ == "__main__":
    print_logo()
    input_path = input("📄 Enter path : ").strip()
    output_file = derive_output_path(input_path)
    asyncio.run(process_credentials(input_path, output_file))
