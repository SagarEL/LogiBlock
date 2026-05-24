import os

def update_colors(directory):
    replacements = {
        # Backgrounds
        'bg-slate-950': 'bg-[#09090b]',
        'bg-slate-900': 'bg-zinc-900',
        'bg-slate-800': 'bg-zinc-800',
        'bg-slate-700': 'bg-zinc-700',
        '#0f172a': '#09090b',
        
        # Primary Accents (Blue -> Fuchsia/Cyan)
        'bg-blue-600': 'bg-fuchsia-600',
        'bg-blue-500': 'bg-fuchsia-500',
        'bg-blue-400': 'bg-fuchsia-400',
        'text-blue-600': 'text-fuchsia-500',
        'text-blue-500': 'text-cyan-400',
        'text-blue-400': 'text-cyan-400',
        'border-blue-500': 'border-fuchsia-500',
        'from-blue-400': 'from-fuchsia-500',
        'to-indigo-400': 'to-cyan-400',
        'to-blue-600': 'to-fuchsia-600',
        
        # Light mode conversion for user/tracking
        'bg-white': 'bg-zinc-900',
        'bg-gray-50': 'bg-zinc-800/50',
        'text-slate-800': 'text-zinc-100',
        'text-slate-700': 'text-zinc-300',
        'text-gray-500': 'text-zinc-400',
        'text-gray-600': 'text-zinc-400',
        'text-gray-800': 'text-zinc-100',
        'border-gray-100': 'border-zinc-800',
        'border-gray-200': 'border-zinc-700',
        'shadow-xl': 'shadow-[0_0_20px_rgba(217,70,239,0.15)]',
        
        # Indigo/Emerald changes for Hashlock PIN
        'bg-indigo-50': 'bg-fuchsia-950/30',
        'border-indigo-200': 'border-fuchsia-500/50',
        'text-indigo-500': 'text-cyan-400',
        'text-indigo-700': 'text-fuchsia-400',
        'border-indigo-100': 'border-fuchsia-500/30'
    }

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                for old, new in replacements.items():
                    new_content = new_content.replace(old, new)
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Updated {filepath}")

if __name__ == '__main__':
    update_colors('templates')
