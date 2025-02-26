import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from youtubedataanalysis import YouTubeAnalyzer, DataVisualizer
import pandas as pd
from datetime import datetime
import numpy as np

class YouTubeAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Channel Analyzer")
        self.root.geometry("1200x800")
        
        # Initialize analyzer
        self.api_key = "AIzaSyAIwXjmWXOEMG47G7ss8tQ4nrChETZ30oY"  # Use your real YouTube Data API key
        self.analyzer = YouTubeAnalyzer(self.api_key)
        self.visualizer = DataVisualizer()
        

        # Channel IDs
        self.channel_ids = [
            "UCnz-ZXXER4jOvuED5trXfEA",  # techTFQ
            "UCLLw7jmFsvfIVaUFsLs8mlQ",  # Luke Barousse
            "UCVgHeVqf7aIlqXQtB83v4sw",  # Nayyar Shaikh
            "UCv9bWHC0DIn-Xb7ALNoOGWQ",  # w3schools
            "UCiT9RITQ9PW6BhXK0y2jaeg",  # Ken Jee
            
        ]
        
        self.setup_gui()
        self.load_channel_data()

    def setup_gui(self):
    # Create main frames
       self.control_frame = ttk.Frame(self.root, padding="10")
       self.control_frame.pack(fill=tk.X)

    # Create a Canvas for scrolling
       self.canvas = tk.Canvas(self.root)
       self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)

    # Create a Frame inside the Canvas to hold the content
       self.scrollable_frame = ttk.Frame(self.canvas)

    # Bind frame resizing to update scroll region
       self.scrollable_frame.bind(
        "<Configure>",
        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    )

    # Add the frame inside the canvas
       self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
       self.canvas.configure(yscrollcommand=self.scrollbar.set)

    # Pack the canvas and scrollbar
       self.canvas.pack(side="left", fill="both", expand=True)
       self.scrollbar.pack(side="right", fill="y")

    # Now, create plot_frame inside the scrollable_frame
       self.plot_frame = ttk.Frame(self.scrollable_frame)
       self.plot_frame.pack(fill=tk.BOTH, expand=True)

    # Control elements (Dropdowns, Buttons, etc.)
       ttk.Label(self.control_frame, text="Channel:").pack(side=tk.LEFT)
       self.channel_var = tk.StringVar()
       self.channel_combo = ttk.Combobox(self.control_frame, textvariable=self.channel_var)
       self.channel_combo.pack(side=tk.LEFT, padx=5)

       ttk.Label(self.control_frame, text="Start Date:").pack(side=tk.LEFT, padx=5)
       self.start_date = DateEntry(self.control_frame, width=12)
       self.start_date.pack(side=tk.LEFT)

       ttk.Label(self.control_frame, text="End Date:").pack(side=tk.LEFT, padx=5)
       self.end_date = DateEntry(self.control_frame, width=12)
       self.end_date.pack(side=tk.LEFT)

    # Analysis buttons
       ttk.Button(self.control_frame, text="Channel Stats", command=self.show_channel_stats).pack(side=tk.LEFT, padx=5)
       ttk.Button(self.control_frame, text="Time Period Analysis", command=self.analyze_time_period).pack(side=tk.LEFT, padx=5)
       ttk.Button(self.control_frame, text="Fourier Analysis", command=self.show_fourier_analysis).pack(side=tk.LEFT, padx=5)

    # Progress bar
       self.progress = ttk.Progressbar(self.control_frame, mode='indeterminate')
       self.progress.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    def load_channel_data(self):
        try:
            self.progress.start()
            self.channel_data = self.analyzer.get_channel_stats(self.channel_ids)
            
            # Convert string numbers to numeric values
            numeric_columns = ['Subscriber', 'Views', 'Total_videos']
            for col in numeric_columns:
                self.channel_data[col] = pd.to_numeric(self.channel_data[col], errors='coerce')
            
            if self.channel_data is not None and not self.channel_data.empty:
                self.channel_combo['values'] = self.channel_data['Channel_name'].tolist()
                self.channel_combo.set(self.channel_data['Channel_name'].iloc[0])
            else:
                messagebox.showerror("Error", "No channel data was loaded")
            self.progress.stop()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load channel data: {str(e)}")
            self.progress.stop()

    def show_channel_stats(self):
        try:
            if self.channel_data is None or self.channel_data.empty:
                messagebox.showerror("Error", "No channel data available")
                return
            
            # Verify numeric data
            if not all(self.channel_data[col].dtype.kind in 'inf' 
                      for col in ['Subscriber', 'Views', 'Total_videos']):
                messagebox.showerror("Error", "Data contains non-numeric values")
                return
            
            self.clear_plot_frame()
            fig = plt.Figure(figsize=(12, 6))
            
            # Subscriber plot
            ax1 = fig.add_subplot(121)
            self.channel_data.plot(
                kind='bar', 
                x='Channel_name', 
                y='Subscriber', 
                ax=ax1,
                color='skyblue'
            )
            ax1.set_title('YouTube Subscribers Count')
            ax1.set_xlabel('Channel Name')
            ax1.set_ylabel('Subscribers')
            ax1.tick_params(axis='x', rotation=45)
            
            # Format y-axis labels with comma separator
            ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
            
            # Video count plot
            ax2 = fig.add_subplot(122)
            self.channel_data.plot(
                kind='bar', 
                x='Channel_name', 
                y='Total_videos', 
                ax=ax2,
                color='lightgreen'
            )
            ax2.set_title('YouTube Videos Count')
            ax2.set_xlabel('Channel Name')
            ax2.set_ylabel('Total Videos')
            ax2.tick_params(axis='x', rotation=45)
            
            # Add value labels on top of bars
            for ax in [ax1, ax2]:
                for container in ax.containers:
                    ax.bar_label(container, fmt='%.0f', padding=3)
            
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, self.plot_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show channel stats: {str(e)}")

    def analyze_time_period(self):
        try:
            self.progress.start()
            channel_name = self.channel_var.get()
            channel_data = self.channel_data[self.channel_data['Channel_name'] == channel_name].iloc[0]
            
            start_date = self.start_date.get_date().strftime('%Y-%m-%d')
            end_date = self.end_date.get_date().strftime('%Y-%m-%d')
            
            video_stats = self.analyzer.get_video_details(channel_data['Playlist_id'])
            period_data, stats = self.analyzer.analyze_time_period(video_stats, start_date, end_date)
            
            if period_data is not None:
                self.clear_plot_frame()
                fig = plt.Figure(figsize=(12, 12))
                
                # Views over time
                ax1 = fig.add_subplot(311)
                ax1.scatter(period_data['Published_date'], period_data['Views'])
                ax1.plot(period_data['Published_date'], period_data['Views'])
                ax1.set_title(f'View Count Analysis ({start_date} to {end_date})\nChannel: {channel_name}')
                ax1.set_xlabel('Publication Date')
                ax1.set_ylabel('Views')
                plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
                
                # FFT Analysis
                ax2 = fig.add_subplot(312)

                # Extract frequency components
                frequencies = stats['FFT_data']['frequencies']
                magnitudes = stats['FFT_data']['magnitudes']
                # Mask to show only positive frequencies
                positive_freq_mask = frequencies > 0
                # Plot the FFT result
                ax2.plot(frequencies[positive_freq_mask], magnitudes[positive_freq_mask], 'r-')
                ax2.set_title('Frequency Spectrum (FFT)')
                ax2.set_xlabel('Frequency (cycles per sample)')
                ax2.set_ylabel('Magnitude')
                ax2.grid(True)
                
                # Statistics text
                ax3 = fig.add_subplot(313)
                ax3.axis('off')
                stats_text = (
                    f"Period Analysis Summary:\n\n"
                    f"Total Videos: {stats['Total_videos']}\n"
                    f"Total Views: {stats['Total_views']:,}\n"
                    f"Average Views: {stats['Average_views']:,.0f}\n"
                    f"Maximum Views: {stats['Max_views']:,}\n"
                    f"Minimum Views: {stats['Min_views']:,}\n\n"
                    f"Most Viewed Video:\n{stats['Most_viewed_video']}\n\n"
                    f"Least Viewed Video:\n{stats['Least_viewed_video']}"
                )
                ax3.text(0.1, 0.9, stats_text, fontsize=10, verticalalignment='top')
                
                fig.tight_layout()
                canvas = FigureCanvasTkAgg(fig, self.plot_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            self.progress.stop()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze time period: {str(e)}")
            self.progress.stop()

    def show_fourier_analysis(self):
        try:
            self.progress.start()
            channel_name = self.channel_var.get()
            channel_data = self.channel_data[self.channel_data['Channel_name'] == channel_name].iloc[0]
            
            video_stats = self.analyzer.get_video_details(channel_data['Playlist_id'])
            self.clear_plot_frame()
            
            fig = plt.Figure(figsize=(12, 8))
            video_stats['Published_date'] = pd.to_datetime(video_stats['Published_date'])
            video_stats = video_stats.sort_values('Published_date')
            
            # Time series plot
            ax1 = fig.add_subplot(211)
            ax1.plot(video_stats['Published_date'], video_stats['Views'], 'b-')
            ax1.set_title(f"View Count Over Time - {channel_name}")
            ax1.set_xlabel('Publication Date')
            ax1.set_ylabel('Views')
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
            
            # FFT plot
            ax2 = fig.add_subplot(212)
            
            views_fft = np.fft.fft(video_stats['Views'].values)
            frequencies = np.fft.fftfreq(len(views_fft))
            positive_freq_mask = frequencies > 0
            ax2.plot(frequencies[positive_freq_mask], 
                    np.abs(views_fft)[positive_freq_mask], 
                    'r-')
            ax2.set_title('Frequency Spectrum (FFT)')
            ax2.set_xlabel('Frequency (cycles per sample)')
            ax2.set_ylabel('Magnitude')
            ax2.grid(True)
            
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, self.plot_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            self.progress.stop()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show Fourier analysis: {str(e)}")
            self.progress.stop()

    def clear_plot_frame(self):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeAnalyzerGUI(root)
    root.mainloop() 
