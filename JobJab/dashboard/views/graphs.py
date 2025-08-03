import pandas as pd
from django.utils import timezone
from plotly import graph_objects as go
import plotly.express as px
from plotly.offline import plot
from django.db.models import Count
from django.db.models.functions import TruncDate


class GraphGenerator:
    """Handles all graph generation logic"""

    @staticmethod
    def create_user_registration_graph(data, time_period):
        df = pd.DataFrame(list(data))

        if df.empty or 'date' not in df.columns or 'count' not in df.columns:
            today = timezone.now().date()
            df = pd.DataFrame([{'date': today, 'count': 0}])

        df['date'] = pd.to_datetime(df['date'])
        df['count'] = df['count'].astype(int)

        date_range = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='D')
        df = df.set_index('date').reindex(date_range, fill_value=0).reset_index()
        df.rename(columns={'index': 'date'}, inplace=True)

        fig = px.line(
            df,
            x='date',
            y='count',
            title=f'User Registrations ({time_period})',
            labels={'date': 'Date', 'count': 'New Users'},
            color_discrete_sequence=['#06BAC5'],
            template='plotly_white'
        )

        fig.update_traces(mode='lines+markers', marker=dict(size=6))
        fig.update_layout(
            hovermode='x unified',
            xaxis_title='Date',
            yaxis_title='New Registrations',
            margin=dict(l=40, r=40, t=80, b=40),
            showlegend=False,
        )

        if len(df) > 1:
            frames = [
                go.Frame(
                    data=[go.Scatter(
                        x=df['date'].iloc[:i],
                        y=df['count'].iloc[:i],
                        mode='lines+markers'
                    )],
                    name=f'frame_{i}'
                )
                for i in range(1, len(df) + 1)
            ]
            fig.frames = frames
            fig.update_layout(
                updatemenus=[dict(
                    type="buttons",
                    showactive=False,
                    buttons=[dict(label="Play", method="animate", args=[None])],
                )]
            )

        return plot(fig, output_type='div', include_plotlyjs='cdn')

    @staticmethod
    def create_certificate_status_graph(certificates):
        """Creates certificate status bar chart"""
        status_counts = certificates.values('is_verified').annotate(count=Count('id'))
        df = pd.DataFrame(list(status_counts))

        if len(df['is_verified'].unique()) < 2:
            all_statuses = pd.DataFrame({
                'is_verified': [True, False],
                'count': [0, 0]
            })
            df = pd.concat([df, all_statuses]).groupby('is_verified').max().reset_index()

        fig = px.bar(
            df,
            x='is_verified',
            y='count',
            color='is_verified',
            title='Certificate Verification Status',
            labels={'is_verified': 'Status', 'count': 'Count'},
            color_discrete_map={True: '#32AE88', False: '#008DAA'},
            width=400,
            height=600
        )

        fig.update_layout(
            hovermode='x unified',
            xaxis=dict(
                tickmode='array',
                tickvals=[False, True],
                ticktext=['Unverified', 'Verified'],
                title='Verification Status'
            ),
            yaxis=dict(title='Number of Certificates'),
            plot_bgcolor='white',
            paper_bgcolor='white',
            hoverlabel=dict(
                bgcolor="white",
                font_size=16,
                font_family="Rockwell"
            )
        )

        config = {
            'displayModeBar': True,
            'modeBarButtonsToAdd': ['hoverclosest', 'hovercompare'],
            'responsive': True
        }

        return plot(fig, output_type='div', config=config, include_plotlyjs='cdn')

    @staticmethod
    def create_service_trend_graph(services, start_date, end_date, arg_getter='created_at'):
        df = pd.DataFrame(
            services.annotate(date=TruncDate(arg_getter))
            .values('date')
            .annotate(count=Count('id'))
        )

        if df.empty:
            df = pd.DataFrame([{'date': start_date.date(), 'count': 0}])

        df['date'] = pd.to_datetime(df['date'])
        date_range = pd.date_range(start=start_date, end=end_date)
        df = df.set_index('date').reindex(date_range, fill_value=0).reset_index()
        df.rename(columns={'index': 'date'}, inplace=True)

        fig = px.bar(
            df, x='date', y='count', title='New Services Over Time',
            labels={'date': 'Date', 'count': 'New Services'},
            color_discrete_sequence=['#4D9DE0']
        )
        return plot(fig, output_type='div', include_plotlyjs='cdn')

    @staticmethod
    def create_availability_status_graph(availabilities):
        df = pd.DataFrame(
            availabilities.values('status').annotate(count=Count('id'))
        )

        if df.empty:
            df = pd.DataFrame({'status': [], 'count': []})

        fig = px.bar(
            df,
            x='status',
            y='count',
            title='Availability Status Distribution',
            labels={'status': 'Status', 'count': 'Count'},
            color_discrete_sequence=['#6c757d']
        )

        fig.update_layout(
            hovermode='x unified',
            xaxis_title='Status',
            yaxis_title='Number of Entries',
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=False
        )

        return plot(fig, output_type='div', include_plotlyjs='cdn')

    @staticmethod
    def create_comment_activity_graph(comments, start_date, end_date):
        df = pd.DataFrame(
            comments.annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
        )

        if df.empty:
            df = pd.DataFrame([{'date': start_date.date(), 'count': 0}])

        df['date'] = pd.to_datetime(df['date'])
        date_range = pd.date_range(start=start_date, end=end_date)
        df = df.set_index('date').reindex(date_range, fill_value=0).reset_index()
        df.rename(columns={'index': 'date'}, inplace=True)

        fig = px.line(
            df, x='date', y='count', title='Comment Activity',
            labels={'date': 'Date', 'count': 'Comments'},
            color_discrete_sequence=['#FF715B']
        )
        return plot(fig, output_type='div', include_plotlyjs='cdn')