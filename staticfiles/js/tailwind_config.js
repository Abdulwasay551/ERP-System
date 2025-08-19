 // Check theme before page load to prevent flash
 if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
} else {
    document.documentElement.classList.remove('dark');
}

tailwind.config = {
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                light: {
                    primary: '#ffffff',
                    secondary: '#f3f4f6',
                    accent: '#3b82f6',
                    text: '#1f2937'
                },
                dark: {
                    '50': '#f8fafc',
                    '100': '#1e293b',
                    '200': '#1a1f35',
                    '300': '#0f172a',
                    '400': '#0d1424',
                    '500': '#0b101f',
                    '600': '#090c19',
                    '700': '#070914',
                    '800': '#05060f',
                    '900': '#030409',
                    primary: '#0f172a',
                    secondary: '#1e293b',
                    accent: '#60a5fa',
                    text: '#f3f4f6'
                },
                blue: {
                    '900': 'rgba(15, 23, 42, 0.6)',
                    '800': 'white',
                    '100': 'rgba(17, 33, 70, 0.75)'
                },
            },
            animation: {
                'gradient': 'gradient 15s ease 1',
                'glow': 'glow 2s ease-in-out 1 alternate'
            },
            keyframes: {
                gradient: {
                    '0%, 100%': {
                        'background-position': '0% 50%'
                    },
                    '50%': {
                        'background-position': '100% 50%'
                    }
                },
                glow: {
                    'from': {
                        'box-shadow': '0 0 20px rgba(59, 130, 246, 0.5)'
                    },
                    'to': {
                        'box-shadow': '0 0 30px rgba(59, 130, 246, 0.8)'
                    }
                }
            }
        }
    }
}