import matplotlib.pyplot as plt
import numpy as np
import random
import os
from matplotlib import font_manager
from matplotlib.ticker import AutoMinorLocator
from scipy.special import expit
from PIL import Image, ImageFilter, ImageDraw, ImageEnhance

class ScatterGeneratorSettings:
    """Encapsulates all configurable settings for scatter plot generation"""
    def __init__(self):
        # Initialize with default values
        self.num_images = 25
        self.min_number_data_series = 1
        self.max_number_data_series = 5
        self.markers = ['o', '^', 's', 'd']
        self.min_points = 15
        self.max_points = 25
        self.x_min, self.x_max = 0, 100
        self.y_min, self.y_max = 0.1, 50
        self.error_min = 2.0
        self.error_max = 4.0
        self.output_format = 'png'
        self.output_dir = 'C:/Users/QuentinMSD/Documents/TEST-SCATTERACT/SCATTER_PLOT_V12A'
        self.mathematical_curve = False
        self.coordinate_tolerance = 1
        self.color_map = 'tab10'
        self.base_font_size = 12
        self.generate_time_series_patterns = True
        self.trend_type_selection = [
            'Linear Saturated', 
            'Logistic Growth', 
            'Exponential Decay',
            'Pharmacokinetic Profile'
        ]
        self.noise_distribution_choice = ['normal', 'uniform', 'triangular']
        self.symmetric_bar = False
        self.grid_customization = ['no_grid', 'standard_grid', 'customized_grid']
        self.grid_style_options = ['major', 'minor', 'both', 'none']
        self.grid_linestyle_options = ['-', '--', ':', '-.']
        self.black_color_selection = ['bw_only', 'color_only', 'bw_color_mixed']
        self.y_label_rotation = False
        self.label_positioning = True
        self.vintage_bw_image = True
        self.vintage_intensity = 0.7
        self.texture_file = 'C:/Users/QuentinMSD/Documents/TEST-SCATTERACT/old_paper.png'
        self.add_error_bars = True
        self.customized_error_bars = ['Standard', 'customized']
        self.random_sized_points = ['Standard', 'random_size']
        self.represent_trend_type_selection = True
        self.customize_trend_type_selection = ['Standard', '-', '--', ':', '-.']
        self.add_minor_tick = True
        self.authorize_semilog = True
        self.customized_size_resolution = True
        
        # PK Profile Parameters
        self.pk_peak_pos_range = (0.3, 0.7)
        self.pk_peak_value_range = (0.6, 0.9)
        self.pk_growth_rate_range = (0.2, 0.4)
        self.pk_decay_rate_range = (0.08, 0.2)
        self.pk_steady_state_range = (0.1, 0.25)
        self.pk_asymmetry_range = (1.5, 2.5)
        
        # Calculated safe boundaries (will be updated later)
        self.x_buffer = None
        self.y_buffer_linear = None
        self.y_buffer_log = 0.75
        self.x_min_safe_linear = None
        self.x_max_safe_linear = None
        self.y_min_safe_linear = None
        self.y_max_safe_linear = None
        self.y_min_safe_log = 0.1 * 1.25
        self.y_max_safe_log = None
        
    def update_calculated_properties(self):
        """Update calculated properties based on current settings"""
        self.x_buffer = 0.02 * (self.x_max - self.x_min)
        self.y_buffer_linear = self.error_max * 1.2
        
        # Linear scale boundaries
        self.x_min_safe_linear = self.x_min + self.x_buffer
        self.x_max_safe_linear = self.x_max - self.x_buffer
        self.y_min_safe_linear = max(self.y_min + self.y_buffer_linear, 0.1)
        self.y_max_safe_linear = self.y_max - self.y_buffer_linear
        
        # Log scale boundaries (multiplicative)
        self.y_max_safe_log = self.y_max / self.y_buffer_log

class ScatterGenerator:
    """Handles the generation of scatter plots based on settings"""
    def __init__(self, settings):
        self.settings = settings
        self.settings.update_calculated_properties()
    
    def get_safe_fonts(self):
        """Get list of safe fonts that can render basic text"""
        system_fonts = font_manager.findSystemFonts()
        safe_fonts = []
        for fpath in system_fonts:
            try:
                font = font_manager.get_font(fpath)
                if font.style.find('Regular') != -1 and font.variant.find('normal') != -1:
                    safe_fonts.append(font.name)
            except:
                continue
        return list(set(safe_fonts)) + ['DejaVu Sans', 'Arial', 'Verdana', 'Times New Roman']
    
    def configure_plot_style(self, ax, title):
        """Configure fonts and label positioning"""
        safe_fonts = self.get_safe_fonts()
        available_fonts = [f for f in safe_fonts if f in font_manager.fontManager.ttflist]
        
        if not available_fonts:
            available_fonts = ['DejaVu Sans', 'Arial', 'Verdana']

        # Font selection
        label_font = random.choice(available_fonts)
        title_font = random.choice(available_fonts)
        
        # Size randomization
        label_size = random.randint(self.settings.base_font_size-2, self.settings.base_font_size+4)
        title_size = random.randint(self.settings.base_font_size+2, self.settings.base_font_size+6)
        tick_size = max(label_size-2, 8)
        
        # Set axis labels first
        ax.set_xlabel('X axis')
        ax.set_ylabel('Y axis')

        # Apply font properties
        ax.xaxis.label.set_fontproperties({'family': label_font, 'size': label_size})
        ax.yaxis.label.set_fontproperties({'family': label_font, 'size': label_size})

        # Y-axis rotation
        if self.settings.y_label_rotation:
            rotation = random.choice([-90, 0, 90])
            ax.yaxis.set_label_text(
                'Y axis', 
                rotation=rotation,
                va='bottom' if rotation != 0 else 'center',
                ha='center'
            )
        
        # Label positioning
        if self.settings.label_positioning:
            x_pos = random.uniform(0.05, 0.95)
            ax.xaxis.set_label_coords(x_pos, -0.03)
            y_pos = random.uniform(0.05, 0.95)
            ax.yaxis.set_label_coords(-0.05, y_pos)
        
        plt.title(title, fontfamily=title_font, fontsize=title_size, pad=20)
        plt.tight_layout(pad=3.0)
    
    def is_function(self, x_values):
        """Check if X-values are unique (vertical line test)"""
        rounded_x = np.round(x_values, int(-np.log10(self.settings.coordinate_tolerance)))
        return len(np.unique(rounded_x)) == len(x_values)
    
    def pharmacokinetic_profile(self, x, params):
        """Generate PK curve with absorption/elimination phases"""
        peak_pos = self.settings.x_min + params['peak_pos'] * (self.settings.x_max - self.settings.x_min)
        peak_val = self.settings.y_min + params['peak_val'] * (self.settings.y_max - self.settings.y_min)
        growth = params['growth_rate']
        decay = params['decay_rate']
        steady = self.settings.y_min + params['steady_state'] * (self.settings.y_max - self.settings.y_min)
        
        growth_phase = peak_val * expit(growth * (x - peak_pos/2))
        decay_phase = steady + (peak_val - steady) * np.exp(-decay * (x - peak_pos))
        return np.where(x < peak_pos, growth_phase, decay_phase)
    
    def validate_pk_params(self, params):
        """Ensure pharmacokinetic validity"""
        t_half_growth = 0.693 / params['growth_rate']
        t_half_decay = 0.693 / params['decay_rate']
        
        if t_half_decay < t_half_growth * 0.5:
            params['decay_rate'] = 0.693 / (t_half_growth * 0.5)
        
        if params['peak_val'] <= params['steady_state']:
            params['peak_val'] = params['steady_state'] * 1.2
        
        return params
    
    def generate_time_series_pattern(self, num_points, trend_type, noise_dist, log_scale):
        """Generate time series data with noise"""
        if log_scale:
            y_min_current = self.settings.y_min_safe_log
            y_max_current = self.settings.y_max_safe_log
        else:
            y_min_current = self.settings.y_min_safe_linear
            y_max_current = self.settings.y_max_safe_linear

        x_min_current = self.settings.x_min_safe_linear
        x_max_current = self.settings.x_max_safe_linear
        x = np.sort(np.random.uniform(x_min_current, x_max_current, num_points))
        
        if trend_type == 'Pharmacokinetic Profile':
            params = {
                'peak_pos': np.random.uniform(*self.settings.pk_peak_pos_range),
                'peak_val': np.random.uniform(*self.settings.pk_peak_value_range),
                'growth_rate': np.random.uniform(*self.settings.pk_growth_rate_range),
                'decay_rate': np.random.uniform(*self.settings.pk_decay_rate_range),
                'steady_state': np.random.uniform(*self.settings.pk_steady_state_range)
            }
            params = self.validate_pk_params(params)
            y_base = self.pharmacokinetic_profile(x, params)
        elif trend_type == 'Linear Saturated':
            slope = np.random.uniform(0.2, 1.5)
            x_mid = np.random.uniform(0.4*x_max_current, 0.8*x_max_current)
            y_base = slope * np.minimum(x, x_mid)
        elif trend_type == 'Logistic Growth':
            max_value = np.random.uniform(0.7*y_max_current, y_max_current)
            growth_rate = np.random.uniform(0.05, 0.2)
            x_mid = np.random.uniform(0.3*x_max_current, 0.7*x_max_current)
            y_base = max_value * expit(growth_rate * (x - x_mid))
        elif trend_type == 'Exponential Decay':
            initial = np.random.uniform(y_min_current, 0.5*y_max_current)
            decay_rate = np.random.uniform(0.08, 0.3)
            steady_state = np.random.uniform(y_min_current, 0.3*y_max_current)
            y_base = steady_state + (initial - steady_state) * np.exp(-decay_rate * x)
        
        # Enhanced noise handling for log scales
        if log_scale:
            noise_scale = np.random.uniform(0.05, 0.15)  # Relative noise
            noise = y_base * np.random.uniform(-noise_scale, noise_scale, len(y_base))
            y = y_base + noise
            y_clipped = np.clip(y, self.settings.y_min_safe_log, self.settings.y_max_safe_log)
        else:
            noise_scale = np.random.uniform(0.05*(y_max_current-y_min_current), 0.15*(y_max_current-y_min_current))
            y = y_base + self.safe_noise(y_base, noise_scale, noise_dist, log_scale)
            y_clipped = np.clip(y, self.settings.y_min_safe_linear, self.settings.y_max_safe_linear)
        
        return x, y_clipped, y_base
    
    def safe_noise(self, y_base, scale, dist, log_scale=False):
        """Generate non-negative noise with absolute values"""
        if dist == 'normal':
            noise = np.random.normal(0, scale, len(y_base))
        elif dist == 'uniform':
            noise = np.random.uniform(-scale, scale, len(y_base))
        elif dist == 'triangular':
            noise = np.random.triangular(-scale, 0, scale, len(y_base))
        if log_scale:
            y_min_current = self.settings.y_min_safe_log
            y_max_current = self.settings.y_max_safe_log
        else:
            y_min_current = self.settings.y_min_safe_linear
            y_max_current = self.settings.y_max_safe_linear

        x_min_current = self.settings.x_min_safe_linear
        x_max_current = self.settings.x_max_safe_linear
        y_noised = np.clip(y_base + noise, y_min_current, y_max_current)
        return y_noised - y_base
    
    def generate_non_overlapping_points(self, num_points, log_scale):
        """Generate points with scale-aware boundaries"""
        if self.settings.generate_time_series_patterns:
            return [], []
        
        # Select appropriate boundaries
        if log_scale:
            y_min_current = self.settings.y_min_safe_log
            y_max_current = self.settings.y_max_safe_log
        else:
            y_min_current = self.settings.y_min_safe_linear
            y_max_current = self.settings.y_max_safe_linear

        x_min_current = self.settings.x_min_safe_linear
        x_max_current = self.settings.x_max_safe_linear

        points = []
        min_distance = 0.05 * max((x_max_current-x_min_current), 
                                (y_max_current-y_min_current)) if not self.settings.mathematical_curve else 0

        for _ in range(num_points):
            attempts = 0
            while attempts < 1000:
                x = random.uniform(x_min_current, x_max_current)
                y = random.uniform(y_min_current, y_max_current)
                overlap = False
                
                for (px, py) in points:
                    x_check = abs(x - px) < (self.settings.coordinate_tolerance if self.settings.mathematical_curve else min_distance)
                    y_check = abs(y - py) < min_distance if not self.settings.mathematical_curve else False
                    if x_check and y_check:
                        overlap = True
                        break
                
                if not overlap:
                    points.append((x, y))
                    break
                attempts += 1
            else:
                print(f"Warning: Could not place point {len(points)+1} after 1000 attempts")
        
        return list(zip(*points)) if points else ([], [])
    
    def generate_errors(self, y_values, log_scale):
        """Generate error bars with proper log/linear scale handling"""
        if log_scale:
            # Handle empty y_values case first
            #if y_values.size == 0:
            #    return [], []
                
            # Convert linear error_min/max to log-scale multiplicative factors
            median_y = np.median(y_values)
            min_factor = max(1.05, 1 + self.settings.error_min/median_y)
            max_factor = 1 + self.settings.error_max/median_y

            if self.settings.symmetric_bar:
                # Symmetric in log space = multiplicative factors
                factors = np.random.uniform(min_factor, max_factor, len(y_values))
                upper = y_values * (factors - 1)
                lower = y_values * (1 - 1/factors)
            else:
                # Asymmetric in log space
                upper_factors = np.random.uniform(1.05, max_factor, len(y_values))
                lower_factors = np.random.uniform(1.05, max_factor, len(y_values))
                upper = y_values * (upper_factors - 1)
                lower = y_values * (1 - 1/lower_factors)
            return upper.tolist(), lower.tolist()
        else:
            # Original linear scale code remains unchanged
            if self.settings.symmetric_bar:
                errors = [random.uniform(self.settings.error_min, self.settings.error_max) for _ in y_values]
                return errors, errors
            else:
                upper = [random.uniform(self.settings.error_min, self.settings.error_max) for _ in y_values]
                lower = [random.uniform(self.settings.error_min, self.settings.error_max/2) for _ in y_values]
                return upper, lower
    
    def configure_grid(self, ax, log_scale):
        """Apply grid customization and minor ticks"""
        grid_option = random.choice(self.settings.grid_customization)
        
        if grid_option == 'no_grid':
            ax.grid(False)
        else:
            if grid_option == 'customized_grid':
                grid_style = random.choice(self.settings.grid_style_options)
                linestyle = random.choice(self.settings.grid_linestyle_options)
                which = 'both' if grid_style == 'both' else ('major' if grid_style == 'major' else 'minor')
                ax.grid(True, which=which, linestyle=linestyle, alpha=0.5)
            else:
                ax.grid(True, linestyle='--', alpha=0.5)
        
        # Handle minor ticks
        if self.settings.add_minor_tick and random.choice([True, False]):
            ax.xaxis.set_minor_locator(AutoMinorLocator())
            if not log_scale:  # Only add y minor ticks for linear scale
                ax.yaxis.set_minor_locator(AutoMinorLocator())
            ax.tick_params(which='minor', length=3, color='gray')
    
    def handle_black_white_mode(self):
        """Determine and validate color mode for current plot"""
        color_mode = random.choice(self.settings.black_color_selection)
        
        if color_mode == 'bw_color_mixed':
            color_mode = random.choice(['bw_only', 'color_only'])
        
        if color_mode == 'bw_only':
            current_max_series = self.settings.max_number_data_series
            available_markers = len(self.settings.markers)
            if current_max_series > available_markers:
                print(f"Warning: Reducing max data series from {current_max_series} to {available_markers} for BW mode")
                current_max_series = available_markers
            return color_mode, current_max_series
        return color_mode, self.settings.max_number_data_series
    
    def apply_vintage_effects(self, img_path, intensity=0.7):
        """Apply vintage effects to BW images"""
        try:
            img = Image.open(img_path).convert('RGB')
            
            if random.random() < 0.8:
                img = img.filter(ImageFilter.GaussianBlur(radius=0.5*intensity))
            
            if random.random() < 0.7:
                width, height = img.size
                overlay = Image.new('RGBA', img.size, (0,0,0,0))
                draw = ImageDraw.Draw(overlay)
                for y in range(0, height, random.randint(3, 7)):
                    draw.line((0, y, width, y), 
                             fill=(0,0,0,random.randint(5, 15)), 
                             width=1)
                img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            
            if random.random() < 0.6:
                try:
                    texture = Image.open(self.settings.texture_file).convert('L').resize(img.size)
                    img = Image.blend(img.convert('RGB'), texture.convert('RGB'), 0.1)
                except FileNotFoundError:
                    print(f"Warning: Texture file {self.settings.texture_file} not found")
            
            if random.random() < 0.9:
                sepia_filter = (
                    0.393 + 0.1*intensity, 0.769, 0.189, 0,
                    0.349, 0.686 + 0.1*intensity, 0.168, 0,
                    0.272, 0.534, 0.131 + 0.1*intensity, 0
                )
                img = img.convert('RGB', matrix=sepia_filter)
            
            if random.random() < 0.5:
                arr = np.array(img).astype(np.float32)
                noise = np.random.normal(0, 20*intensity, arr.shape)
                noisy = np.clip(arr + noise, 0, 255).astype(np.uint8)
                img = Image.fromarray(noisy)
            
            enhancer = ImageEnhance.Brightness(img)
            return enhancer.enhance(1 - 0.2*intensity)
        
        except Exception as e:
            print(f"Error applying vintage effects: {str(e)}")
            return Image.open(img_path).convert('RGB')
    
    def save_coordinate_file(self, x_data, y_data, filename):
        """Save coordinates to a sorted text file"""
        combined = sorted(zip(x_data, y_data), 
                         key=lambda p: (round(p[0], 6), p[1]))
        with open(filename, 'w') as f:
            f.write("X coordinates\tY coordinates\n")
            for x, y in combined:
                f.write(f"{x:.6f}\t{y:.6f}\n")
    
    def save_error_file(self, upper_errors, lower_errors, filename):
        """Save error values to a text file"""
        with open(filename, 'w') as f:
            f.write("Upper error values\tLower error values\n")
            for upper, lower in zip(upper_errors, lower_errors):
                f.write(f"{upper:.6f}\t{lower:.6f}\n")
    
    def save_ticks_file(self, ticks, filename):
        """Save tick coordinates to a text file"""
        with open(filename, 'w') as f:
            for tick in ticks:
                f.write(f"{tick:.6f}\n")
    
    def save_data_files(self, plot_number, all_series, all_errors):
        """Save all data files for a plot"""
        for series_idx, (x_coords, y_coords) in enumerate(all_series):
            # Save coordinates
            data_filename = os.path.join(
                self.settings.output_dir,
                f'scatter_plot_data_{plot_number:03d}_series_{series_idx+1}.txt'
            )
            self.save_coordinate_file(x_coords, y_coords, data_filename)
            
            # Save errors if applicable
            if self.settings.add_error_bars and len(all_errors) > series_idx:
                error_filename = os.path.join(
                    self.settings.output_dir,
                    f'error_bar_value__plot_data_{plot_number:03d}_series_{series_idx+1}.txt'
                )
                upper_errors, lower_errors = all_errors[series_idx]
                self.save_error_file(upper_errors, lower_errors, error_filename)
    
    def save_tick_files(self, plot_number, x_ticks_major, x_ticks_minor, y_ticks_major, y_ticks_minor):
        """Save all tick coordinate files for a plot"""
        # Save X-axis ticks
        if len(x_ticks_major) > 0:
            x_major_filename = os.path.join(
                self.settings.output_dir,
                f'tick_x_major_{plot_number:03d}.txt'
            )
            self.save_ticks_file(x_ticks_major, x_major_filename)
        
        if len(x_ticks_minor) > 0:
            x_minor_filename = os.path.join(
                self.settings.output_dir,
                f'tick_x_minor_{plot_number:03d}.txt'
            )
            self.save_ticks_file(x_ticks_minor, x_minor_filename)
        
        # Save Y-axis ticks
        if len(y_ticks_major) > 0:
            y_major_filename = os.path.join(
                self.settings.output_dir,
                f'tick_y_major_{plot_number:03d}.txt'
            )
            self.save_ticks_file(y_ticks_major, y_major_filename)
        
        if len(y_ticks_minor) > 0:
            y_minor_filename = os.path.join(
                self.settings.output_dir,
                f'tick_y_minor_{plot_number:03d}.txt'
            )
            self.save_ticks_file(y_ticks_minor, y_minor_filename)
    
    def create_scatter_plot(self, plot_number):
        """Create scatter plot with new features"""
        # Initialize log messages for this plot
        log_messages = []
        
        # Randomize size/resolution if enabled
        if self.settings.customized_size_resolution:
            figsize = (random.uniform(10, 14), random.uniform(6, 8))
            dpi = random.choice([100, 150, 200])
            bbox_pad = random.uniform(0.1, 0.3)
        else:
            figsize = (12, 7)
            dpi = 150
            bbox_pad = 0.1
            
        fig, ax = plt.subplots(figsize=figsize)
        color_mode, current_max_series = self.handle_black_white_mode()
        
        # Semilog scale handling
        use_log_scale = False
        if self.settings.authorize_semilog and random.choice([True, False]):
            ax.set_yscale('log')
            use_log_scale = True
            ax.set_ylim(max(self.settings.y_min*self.settings.y_buffer_log, 0.1), 
                        self.settings.y_max/self.settings.y_buffer_log)
        
        try:
            cmap = plt.colormaps[self.settings.color_map]
        except AttributeError:
            cmap = plt.get_cmap(self.settings.color_map)
        
        num_series = random.randint(self.settings.min_number_data_series, current_max_series)
        all_series_data = []
        all_series_errors = []
        
        if color_mode == 'bw_only':
            series_colors = ['black'] * num_series
            edge_colors = ['black'] * num_series
        else:
            series_colors = [cmap(i/num_series) for i in range(num_series)]
            edge_colors = ['black'] * num_series

        if self.settings.generate_time_series_patterns:
            trend_type = random.choice(self.settings.trend_type_selection)
            noise_dist = random.choice(self.settings.noise_distribution_choice)
        else:
            trend_type = noise_dist = None
        
        # Error bar configuration
        error_style = random.choice(self.settings.customized_error_bars) if self.settings.add_error_bars else None
        cap_size = 3 if error_style == 'Standard' else random.choice([2, 4, 5])
        cap_thick = 1 if error_style == 'Standard' else random.randint(1, 3)
        error_every = 1  # Always show all error bars
        
        # Marker size configuration
        size_style = random.choice(self.settings.random_sized_points)
        if size_style == 'random_size':
            base_size = random.randint(6, 7)
            size_range = (base_size, base_size + random.randint(1, 6))
        else:
            size_range = (8, 8)

        for series_idx in range(num_series):
            num_points = random.randint(self.settings.min_points, self.settings.max_points)
            
            if self.settings.generate_time_series_patterns:
                x_coords, y_coords, y_base = self.generate_time_series_pattern(
                    num_points, trend_type, noise_dist, use_log_scale
                )
            else:
                x_coords, y_coords = self.generate_non_overlapping_points(num_points, log_scale=use_log_scale)
                y_base = None
            
            errors = self.generate_errors(y_coords, use_log_scale) if self.settings.add_error_bars else None
            current_marker = random.choice(self.settings.markers)
            
            if size_style == 'random_size':
                size = random.uniform(size_range[0], size_range[1])
                sizes = size
            else:
                sizes = 8
            
            plot_args = {
                'x': x_coords,
                'y': y_coords,
                'fmt': current_marker,
                'color': series_colors[series_idx],
                'markersize': sizes if isinstance(sizes, np.ndarray) else 8,
                'ecolor': series_colors[series_idx] if color_mode != 'bw_only' else 'black',
                'elinewidth': 1,
                'alpha': 0.7,
                'markeredgecolor': edge_colors[series_idx],
                'label': f'Series {series_idx+1}'
            }
            
            if self.settings.add_error_bars:
                upper_errors, lower_errors = errors
                plot_args['yerr'] = [lower_errors, upper_errors]
                plot_args['capsize'] = cap_size
                plot_args['capthick'] = cap_thick
                plot_args['errorevery'] = error_every
                all_series_errors.append((upper_errors, lower_errors))
            
            ax.errorbar(**plot_args)
            
            if (self.settings.generate_time_series_patterns and 
                self.settings.represent_trend_type_selection and 
                y_base is not None):
                line_style = random.choice(self.settings.customize_trend_type_selection)
                if line_style == 'Standard':
                    line_style = '-'
                ax.plot(x_coords, y_base, 
                        linestyle=line_style,
                        color=series_colors[series_idx],
                        alpha=0.5,
                        label=f'Trend {series_idx+1}')
            
            all_series_data.append((x_coords, y_coords))

        ax.set_xlim(self.settings.x_min, self.settings.x_max)
        if not use_log_scale:
            ax.set_ylim(self.settings.y_min, self.settings.y_max)
        
        title = f"Example No. {plot_number:03d} of a scatter plot with error bars"
        self.configure_grid(ax, use_log_scale)
        self.configure_plot_style(ax, title)
        ax.legend(loc='best', framealpha=0.9)
        
        # Capture tick coordinates
        x_ticks_major = ax.get_xticks().tolist()
        x_ticks_minor = ax.get_xticks(minor=True).tolist()
        y_ticks_major = ax.get_yticks().tolist()
        y_ticks_minor = ax.get_yticks(minor=True).tolist()
        
        # Create log message for vertical line tests
        test_results = []
        for series_idx, (x_coords, y_coords) in enumerate(all_series_data):
            test_results.append(self.is_function(np.array(x_coords)))
        
        result_str = ", ".join([f"Series {i+1}: {'PASS' if r else 'FAIL'}" 
                              for i, r in enumerate(test_results)])
        log_messages.append(f"Plot {plot_number:03d} [Series: {len(all_series_data)}]")
        log_messages.append(f"Vertical Line Tests: {result_str}")
        log_messages.append(f"Image size: {figsize}, DPI: {dpi}")
        
        return (fig, all_series_data, all_series_errors, color_mode, dpi, bbox_pad,
                log_messages, x_ticks_major, x_ticks_minor, y_ticks_major, y_ticks_minor)
    
    def generate_all_plots(self):
        """Main function to generate all plots and data files"""
        if self.settings.error_max > (self.settings.y_max - self.settings.y_min) / 2:
            new_error_max = (self.settings.y_max - self.settings.y_min) / 2
            print(f"Adjusted error_max from {self.settings.error_max} to {new_error_max} to prevent overflow")
            self.settings.error_max = new_error_max
        
        os.makedirs(self.settings.output_dir, exist_ok=True)
        
        for i in range(self.settings.num_images):
            plot_number = i + 1
            (fig, all_series, all_errors, color_mode, dpi, bbox_pad,
             log_messages, x_ticks_major, x_ticks_minor, y_ticks_major, y_ticks_minor) = self.create_scatter_plot(plot_number)
            
            temp_filename = os.path.join(self.settings.output_dir, f'temp_scatter_plot_{plot_number:03d}.png')
            img_filename = os.path.join(self.settings.output_dir, f'scatter_plot_{plot_number:03d}.{self.settings.output_format}')
            
            for fpath in [temp_filename, img_filename]:
                if os.path.exists(fpath):
                    os.remove(fpath)
            
            # Save with customized parameters
            fig.savefig(temp_filename, dpi=dpi, bbox_inches='tight', pad_inches=bbox_pad)
            plt.close(fig)
            
            # Apply vintage effects if enabled
            if (self.settings.vintage_bw_image and 
                color_mode == 'bw_only' and 
                random.random() < 0.7):
                try:
                    final_img = self.apply_vintage_effects(temp_filename, self.settings.vintage_intensity)
                    final_img.save(img_filename)
                except Exception as e:
                    print(f"Error applying vintage effects: {e}")
                    os.replace(temp_filename, img_filename)
                finally:
                    if os.path.exists(temp_filename):
                        os.remove(temp_filename)
            else:
                os.replace(temp_filename, img_filename)
            
            # Save all data files
            self.save_data_files(plot_number, all_series, all_errors)
            
            # Save all tick files
            self.save_tick_files(plot_number, x_ticks_major, x_ticks_minor, y_ticks_major, y_ticks_minor)
            
            # Print log messages
            for message in log_messages:
                print(message)
            
            # Print file paths
            print(f"Image saved: {img_filename}")
            for series_idx in range(len(all_series)):
                data_file = f'scatter_plot_data_{plot_number:03d}_series_{series_idx+1}.txt'
                print(f"Data saved: {data_file}")
                if self.settings.add_error_bars:
                    error_file = f'error_bar_value__plot_data_{plot_number:03d}_series_{series_idx+1}.txt'
                    print(f"Error data saved: {error_file}")
            
            # Print tick files
            if len(x_ticks_major) > 0:
                print(f"X-axis major ticks saved: tick_x_major_{plot_number:03d}.txt")
            if len(x_ticks_minor) > 0:
                print(f"X-axis minor ticks saved: tick_x_minor_{plot_number:03d}.txt")
            if len(y_ticks_major) > 0:
                print(f"Y-axis major ticks saved: tick_y_major_{plot_number:03d}.txt")
            if len(y_ticks_minor) > 0:
                print(f"Y-axis minor ticks saved: tick_y_minor_{plot_number:03d}.txt")
            print()
        
        print(f"Successfully generated {self.settings.num_images} plots in '{self.settings.output_dir}'")

def main():
    """Entry point for command-line execution"""
    settings = ScatterGeneratorSettings()
    generator = ScatterGenerator(settings)
    generator.generate_all_plots()

if __name__ == '__main__':
    main()