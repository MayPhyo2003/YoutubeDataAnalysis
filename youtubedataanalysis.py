import os
from googleapiclient.discovery import build
import pandas as pd 
import seaborn as sns
import matplotlib.pyplot as plt 
import numpy as np
import matplotlib.ticker as mticker
from scipy.fft import fft
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import asyncio
import aiohttp
import time

class YouTubeAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        
    async def fetch_video_data(self, session, video_id):
        """Fetch data for a single video using aiohttp"""
        url = f"https://www.googleapis.com/youtube/v3/videos"
        params = {
            'part': 'snippet,statistics',
            'id': video_id,
            'key': self.api_key
        }
        
        try:
            async with session.get(url, params=params) as response:
                data = await response.json()
                if 'items' in data and data['items']:
                    video = data['items'][0]
                    return {
                        'Title': video['snippet']['title'],
                        'Published_date': video['snippet']['publishedAt'],
                        'Views': int(video['statistics'].get('viewCount', 0))
                    }
        except Exception as e:
            return None

    async def fetch_all_videos(self, video_ids):
        """Fetch data for multiple videos in parallel"""
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_video_data(session, vid) for vid in video_ids]
            results = await asyncio.gather(*tasks)
            return [r for r in results if r is not None]

    async def get_video_details_async(self, playlist_id):
        """Asynchronously fetch all video details for a playlist"""
        video_ids = []
        next_page_token = None
        
        while True:
            try:
                request = self.youtube.playlistItems().list(
                    part="contentDetails",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                
                video_ids.extend([item['contentDetails']['videoId'] 
                                for item in response['items']])
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except Exception:
                break

        video_data = await self.fetch_all_videos(video_ids)
        return pd.DataFrame(video_data)

    def get_video_details(self, playlist_id):
        """Synchronous wrapper for async video details fetching"""
        return asyncio.run(self.get_video_details_async(playlist_id))

    def get_channel_stats(self, channel_ids):
        """Fetch basic statistics for YouTube channels"""
        all_data = []
        
        try:
            for i in range(0, len(channel_ids), 50):
                batch_ids = channel_ids[i:i+50]
                request = self.youtube.channels().list(
                    part="snippet,contentDetails,statistics",
                    id=",".join(batch_ids)
                )
                response = request.execute()

                for item in response["items"]:
                    stats = item["statistics"]
                    data = {
                        "Channel_name": item["snippet"]["title"],
                        "Subscriber": int(stats.get("subscriberCount", 0)),
                        "Views": int(stats.get("viewCount", 0)),
                        "Total_videos": int(stats.get("videoCount", 0)),
                        "Playlist_id": item["contentDetails"]["relatedPlaylists"]["uploads"]
                    }
                    all_data.append(data)

            return pd.DataFrame(all_data)
        except Exception:
            return pd.DataFrame()

    def analyze_time_period(self, video_data, start_date, end_date):
        """Analyze video performance within a specific time period"""
        try:
            video_data['Published_date'] = pd.to_datetime(video_data['Published_date']).dt.tz_localize(None)
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            
            mask = (video_data['Published_date'] >= start_date) & (video_data['Published_date'] <= end_date)
            period_data = video_data.loc[mask].copy()
            
            if period_data.empty:
                return None, None
            
            period_data = period_data.sort_values('Published_date')
            
            views_fft = np.fft.fft(period_data['Views'].values)
            frequencies = np.fft.fftfreq(len(views_fft))
            
            stats = {
                'Total_videos': len(period_data),
                'Total_views': period_data['Views'].sum(),
                'Average_views': period_data['Views'].mean(),
                'Max_views': period_data['Views'].max(),
                'Min_views': period_data['Views'].min(),
                'Most_viewed_video': period_data.loc[period_data['Views'].idxmax(), 'Title'],
                'Least_viewed_video': period_data.loc[period_data['Views'].idxmin(), 'Title'],
                'FFT_data': {
                    'frequencies': frequencies,
                    'magnitudes': np.abs(views_fft)
                }
            }
            
            return period_data, stats
            
        except Exception:
            return None, None

class DataVisualizer:
    @staticmethod
    def plot_channel_stats(channel_data):
        """Plot basic channel statistics"""
        plt.figure(figsize=(12, 6))
        channel_data.plot(kind='bar', x='Channel_name', y=['Subscriber', 'Total_videos'])
        plt.title('YouTube Channel Statistics')
        plt.xlabel('Channel Name')
        plt.ylabel('Count')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_fourier_analysis(df_videos, channel_name):
        """Plot time series analysis with FFT"""
        # Prepare data
        df_videos['Published_date'] = pd.to_datetime(df_videos['Published_date'])
        df_videos = df_videos.sort_values('Published_date')
        
        # Perform FFT
        views_fft = fft(df_videos['Views'].values)
        frequencies = np.fft.fftfreq(len(views_fft))
        
        # Create plots
        plt.figure(figsize=(15, 10))
        
        # Time series plot
        plt.subplot(2, 1, 1)
        plt.plot(df_videos['Published_date'], df_videos['Views'], 'b-', linewidth=1)
        plt.title(f"View Count Over Time - {channel_name}")
        plt.xlabel('Publication Date')
        plt.ylabel('Views')
        plt.grid(True)
        plt.xticks(rotation=45)
        
        # FFT plot
        plt.subplot(2, 1, 2)
        # Only plot positive frequencies up to Nyquist frequency
        positive_freq_mask = frequencies > 0
        plt.plot(frequencies[positive_freq_mask], 
                np.abs(views_fft)[positive_freq_mask], 
                'r-', linewidth=1)
        plt.title('Frequency Spectrum (FFT)')
        plt.xlabel('Frequency (cycles per sample)')
        plt.ylabel('Magnitude')
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_time_period_analysis(period_data, stats, channel_name, start_date, end_date):
        """Plot analysis for a specific time period including FFT"""
        if period_data is None or stats is None:
            return

        # Create figure with subplots
        fig = plt.figure(figsize=(15, 15))
        
        # 1. Views over time
        plt.subplot(3, 1, 1)
        sns.scatterplot(data=period_data, x='Published_date', y='Views')
        plt.plot(period_data['Published_date'], period_data['Views'])
        plt.title(f'View Count Analysis ({start_date} to {end_date})\nChannel: {channel_name}')
        plt.xlabel('Publication Date')
        plt.ylabel('Views')
        plt.xticks(rotation=45)
        plt.grid(True)
        
        # 2. FFT Analysis
        plt.subplot(3, 1, 2)
        frequencies = stats['FFT_data']['frequencies']
        magnitudes = stats['FFT_data']['magnitudes']
        # Plot only positive frequencies
        positive_freq_mask = frequencies > 0
        plt.plot(frequencies[positive_freq_mask], 
                magnitudes[positive_freq_mask], 
                'r-', linewidth=1)
        plt.title('Frequency Spectrum (FFT)')
        plt.xlabel('Frequency (cycles per sample)')
        plt.ylabel('Magnitude')
        plt.grid(True)
        
        # 3. Statistics text
        plt.subplot(3, 1, 3)
        plt.axis('off')
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
        plt.text(0.1, 0.9, stats_text, fontsize=10, verticalalignment='top')
        
        plt.tight_layout()
        plt.show()

def get_date_input():
    """Get date input from user with validation"""
    while True:
        try:
            start_date = input("Enter start date (YYYY-MM-DD): ")
            end_date = input("Enter end date (YYYY-MM-DD): ")
            
            # Validate dates
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            
            if end < start:
                print("End date must be after start date!")
                continue
                
            return start_date, end_date
            
        except ValueError:
            print("Invalid date format! Please use YYYY-MM-DD format.")
            continue

def get_channel_selection(channel_data):
    """Let user select which channels to analyze"""
    print("\nAvailable channels:")
    for idx, channel in channel_data.iterrows():
        print(f"{idx + 1}. {channel['Channel_name']}")
    
    while True:
        try:
            print("\nEnter channel numbers to analyze (comma-separated) or 'all' for all channels")
            selection = input("Your selection: ").strip().lower()
            
            if selection == 'all':
                return channel_data.index.tolist()
            
            selected_indices = [int(idx.strip()) - 1 for idx in selection.split(',')]
            if all(0 <= idx < len(channel_data) for idx in selected_indices):
                return selected_indices
            else:
                print("Invalid channel number(s)! Please try again.")
                
        except ValueError:
            print("Invalid input! Please enter numbers separated by commas or 'all'")

def main():
    # Configuration
    api_key = "AIzaSyAIwXjmWXOEMG47G7ss8tQ4nrChETZ30oY"  # Replace with your API key
    channel_ids = [
        "UCnz-ZXXER4jOvuED5trXfEA",  # techTFQ
        "UCLLw7jmFsvfIVaUFsLs8mlQ",  # Luke Barousse
        "UCVgHeVqf7aIlqXQtB83v4sw",  # Nayyar Shaikh
        "UCP235oUhop0rvk7wuJTjx6A",  # TBH Labs
        "UCiT9RITQ9PW6BhXK0y2jaeg",  # Ken Jee
        
    ]

    # Initialize analyzer
    analyzer = YouTubeAnalyzer(api_key)
    visualizer = DataVisualizer()

    try:
        # Get channel statistics
        print("Fetching channel data...")
        channel_data = analyzer.get_channel_stats(channel_ids)
        
        # Convert numeric columns
        numeric_columns = ['Subscriber', 'Views', 'Total_videos']
        for col in numeric_columns:
            channel_data[col] = pd.to_numeric(channel_data[col])

        while True:
            print("\n=== YouTube Channel Analysis ===")
            print("1. View all channel statistics")
            print("2. Analyze specific time period")
            print("3. Run Fourier analysis")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ")
            
            if choice == '1':
                visualizer.plot_channel_stats(channel_data)
                
            elif choice == '2':
                # Get date range from user
                start_date, end_date = get_date_input()
                
                # Get channel selection from user
                selected_indices = get_channel_selection(channel_data)
                
                # Analyze selected channels
                for idx in selected_indices:
                    channel = channel_data.iloc[idx]
                    print(f"\nAnalyzing {channel['Channel_name']}...")
                    video_stats = analyzer.get_video_details(channel['Playlist_id'])
                    
                    period_data, stats = analyzer.analyze_time_period(
                        video_stats, 
                        start_date, 
                        end_date
                    )
                    
                    if period_data is not None:
                        visualizer.plot_time_period_analysis(
                            period_data,
                            stats,
                            channel['Channel_name'],
                            start_date,
                            end_date
                        )
                        
            elif choice == '3':
                # Get channel selection for Fourier analysis
                selected_indices = get_channel_selection(channel_data)
                
                for idx in selected_indices:
                    channel = channel_data.iloc[idx]
                    print(f"\nAnalyzing {channel['Channel_name']}...")
                    video_stats = analyzer.get_video_details(channel['Playlist_id'])
                    visualizer.plot_fourier_analysis(video_stats, channel['Channel_name'])
                    
            elif choice == '4':
                print("\nThank you for using YouTube Channel Analysis!")
                break
                
            else:
                print("\nInvalid choice! Please try again.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

