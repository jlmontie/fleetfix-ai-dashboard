"""
Plotly Chart Generator
Converts query results + chart config into Plotly JSON specifications.
"""

from typing import Dict, List, Any, Optional
import json


class PlotlyGenerator:
    """Generates Plotly chart configurations from data and chart specs."""
    
    def __init__(self):
        # Default color scheme (professional blues/grays)
        self.colors = {
            'primary': '#2563eb',      # Blue
            'secondary': '#64748b',    # Slate
            'success': '#10b981',      # Green
            'warning': '#f59e0b',      # Amber
            'danger': '#ef4444',       # Red
            'palette': [               # For multiple series
                '#2563eb', '#8b5cf6', '#06b6d4', '#10b981', 
                '#f59e0b', '#ef4444', '#ec4899', '#6366f1'
            ]
        }
    
    def generate(
        self, 
        chart_config: Dict[str, Any], 
        results: List[Dict[str, Any]], 
        columns: List[str]
    ) -> Dict[str, Any]:
        """
        Generate Plotly configuration from chart config and data.
        
        Args:
            chart_config: Chart configuration from AI
            results: Query results
            columns: Column names
            
        Returns:
            Plotly JSON specification
        """
        chart_type = chart_config.get('type', 'table')
        
        if chart_type == 'line':
            return self._generate_line_chart(chart_config, results, columns)
        elif chart_type == 'bar':
            return self._generate_bar_chart(chart_config, results, columns)
        elif chart_type == 'grouped_bar':
            return self._generate_grouped_bar_chart(chart_config, results, columns)
        elif chart_type == 'scatter':
            return self._generate_scatter_plot(chart_config, results, columns)
        elif chart_type == 'map':
            return self._generate_map(chart_config, results, columns)
        elif chart_type == 'metric':
            return self._generate_metric_card(chart_config, results, columns)
        else:  # table or unknown
            return self._generate_table(chart_config, results, columns)
    
    def _generate_line_chart(
        self, 
        chart_config: Dict[str, Any], 
        results: List[Dict[str, Any]], 
        columns: List[str]
    ) -> Dict[str, Any]:
        """Generate line chart for time series data."""
        x_column = chart_config.get('x_column') or columns[0]
        y_columns = chart_config.get('y_columns', [])
        
        # If no y_columns specified, use all numeric columns except x
        if not y_columns:
            y_columns = [col for col in columns if col != x_column]
        
        # Extract x values
        x_values = [row.get(x_column) for row in results]
        
        # Create traces for each y column
        traces = []
        for idx, y_col in enumerate(y_columns):
            y_values = [row.get(y_col) for row in results]
            
            traces.append({
                'x': x_values,
                'y': y_values,
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': self._format_label(y_col),
                'line': {
                    'color': self.colors['palette'][idx % len(self.colors['palette'])],
                    'width': 2
                },
                'marker': {
                    'size': 6
                }
            })
        
        layout = {
            'title': chart_config.get('title', 'Time Series'),
            'xaxis': {
                'title': self._format_label(x_column),
                'showgrid': True,
                'gridcolor': '#e5e7eb'
            },
            'yaxis': {
                'title': chart_config.get('y_label', 'Value'),
                'showgrid': True,
                'gridcolor': '#e5e7eb'
            },
            'hovermode': 'x unified',
            'plot_bgcolor': '#ffffff',
            'paper_bgcolor': '#ffffff',
            'font': {
                'family': 'Inter, system-ui, sans-serif',
                'size': 12,
                'color': '#1f2937'
            },
            'margin': {'l': 60, 'r': 40, 't': 60, 'b': 60}
        }
        
        return {
            'data': traces,
            'layout': layout,
            'config': {
                'responsive': True,
                'displayModeBar': True,
                'displaylogo': False
            }
        }
    
    def _generate_bar_chart(
        self, 
        chart_config: Dict[str, Any], 
        results: List[Dict[str, Any]], 
        columns: List[str]
    ) -> Dict[str, Any]:
        """Generate bar chart for categorical comparisons."""
        category_column = chart_config.get('category_column') or chart_config.get('x_column') or columns[0]
        value_column = chart_config.get('value_column') or chart_config.get('y_columns', [columns[1]])[0]
        
        # Extract data
        categories = [row.get(category_column) for row in results]
        values = [row.get(value_column) for row in results]
        
        # Sort by value descending
        sorted_data = sorted(zip(categories, values), key=lambda x: x[1] or 0, reverse=True)
        categories, values = zip(*sorted_data) if sorted_data else ([], [])
        
        trace = {
            'x': list(categories),
            'y': list(values),
            'type': 'bar',
            'marker': {
                'color': self.colors['primary'],
                'line': {
                    'color': self.colors['primary'],
                    'width': 1
                }
            },
            'text': [f"{v:,.0f}" if v else "" for v in values],
            'textposition': 'outside'
        }
        
        layout = {
            'title': chart_config.get('title', 'Comparison'),
            'xaxis': {
                'title': self._format_label(category_column),
                'showgrid': False
            },
            'yaxis': {
                'title': self._format_label(value_column),
                'showgrid': True,
                'gridcolor': '#e5e7eb'
            },
            'plot_bgcolor': '#ffffff',
            'paper_bgcolor': '#ffffff',
            'font': {
                'family': 'Inter, system-ui, sans-serif',
                'size': 12,
                'color': '#1f2937'
            },
            'margin': {'l': 60, 'r': 40, 't': 60, 'b': 100}
        }
        
        return {
            'data': [trace],
            'layout': layout,
            'config': {
                'responsive': True,
                'displayModeBar': True,
                'displaylogo': False
            }
        }
    
    def _generate_grouped_bar_chart(
        self, 
        chart_config: Dict[str, Any], 
        results: List[Dict[str, Any]], 
        columns: List[str]
    ) -> Dict[str, Any]:
        """Generate grouped bar chart for multiple metrics per category."""
        category_column = chart_config.get('category_column') or chart_config.get('x_column') or columns[0]
        value_columns = chart_config.get('value_columns') or chart_config.get('y_columns', columns[1:])
        
        # Extract categories
        categories = [row.get(category_column) for row in results]
        
        # Create trace for each value column
        traces = []
        for idx, value_col in enumerate(value_columns):
            values = [row.get(value_col) for row in results]
            
            traces.append({
                'x': categories,
                'y': values,
                'type': 'bar',
                'name': self._format_label(value_col),
                'marker': {
                    'color': self.colors['palette'][idx % len(self.colors['palette'])]
                }
            })
        
        layout = {
            'title': chart_config.get('title', 'Multi-Metric Comparison'),
            'xaxis': {
                'title': self._format_label(category_column),
                'showgrid': False
            },
            'yaxis': {
                'title': 'Values',
                'showgrid': True,
                'gridcolor': '#e5e7eb'
            },
            'barmode': 'group',
            'plot_bgcolor': '#ffffff',
            'paper_bgcolor': '#ffffff',
            'font': {
                'family': 'Inter, system-ui, sans-serif',
                'size': 12,
                'color': '#1f2937'
            },
            'margin': {'l': 60, 'r': 40, 't': 60, 'b': 100}
        }
        
        return {
            'data': traces,
            'layout': layout,
            'config': {
                'responsive': True,
                'displayModeBar': True,
                'displaylogo': False
            }
        }
    
    def _generate_scatter_plot(
        self, 
        chart_config: Dict[str, Any], 
        results: List[Dict[str, Any]], 
        columns: List[str]
    ) -> Dict[str, Any]:
        """Generate scatter plot for correlation analysis."""
        x_column = chart_config.get('x_column') or columns[0]
        y_column = chart_config.get('y_column') or chart_config.get('y_columns', [columns[1]])[0]
        label_column = chart_config.get('label_column')
        
        # Extract data
        x_values = [row.get(x_column) for row in results]
        y_values = [row.get(y_column) for row in results]
        
        # Create hover text
        if label_column:
            hover_text = [f"{row.get(label_column)}<br>{x_column}: {row.get(x_column)}<br>{y_column}: {row.get(y_column)}" 
                         for row in results]
        else:
            hover_text = [f"{x_column}: {row.get(x_column)}<br>{y_column}: {row.get(y_column)}" 
                         for row in results]
        
        trace = {
            'x': x_values,
            'y': y_values,
            'type': 'scatter',
            'mode': 'markers',
            'marker': {
                'size': 10,
                'color': self.colors['primary'],
                'opacity': 0.6,
                'line': {
                    'color': 'white',
                    'width': 1
                }
            },
            'text': hover_text,
            'hoverinfo': 'text'
        }
        
        layout = {
            'title': chart_config.get('title', 'Correlation Analysis'),
            'xaxis': {
                'title': self._format_label(x_column),
                'showgrid': True,
                'gridcolor': '#e5e7eb'
            },
            'yaxis': {
                'title': self._format_label(y_column),
                'showgrid': True,
                'gridcolor': '#e5e7eb'
            },
            'hovermode': 'closest',
            'plot_bgcolor': '#ffffff',
            'paper_bgcolor': '#ffffff',
            'font': {
                'family': 'Inter, system-ui, sans-serif',
                'size': 12,
                'color': '#1f2937'
            },
            'margin': {'l': 60, 'r': 40, 't': 60, 'b': 60}
        }
        
        return {
            'data': [trace],
            'layout': layout,
            'config': {
                'responsive': True,
                'displayModeBar': True,
                'displaylogo': False
            }
        }
    
    def _generate_map(
        self, 
        chart_config: Dict[str, Any], 
        results: List[Dict[str, Any]], 
        columns: List[str]
    ) -> Dict[str, Any]:
        """Generate map for geographic data."""
        lat_column = chart_config.get('lat_column') or chart_config.get('x_column') or self._find_column(columns, ['lat', 'latitude', 'gps_lat'])
        lon_column = chart_config.get('lon_column') or self._find_column(chart_config.get('y_columns', []), ['lon', 'longitude', 'gps_lon']) or self._find_column(columns, ['lon', 'longitude', 'gps_lon'])
        
        # Extract coordinates
        lats = [row.get(lat_column) for row in results if row.get(lat_column) is not None]
        lons = [row.get(lon_column) for row in results if row.get(lon_column) is not None]
        
        # Create hover text with all other columns
        hover_texts = []
        for row in results:
            if row.get(lat_column) is not None and row.get(lon_column) is not None:
                text_parts = [f"<b>{k}</b>: {v}" for k, v in row.items() 
                            if k not in [lat_column, lon_column] and v is not None]
                hover_texts.append("<br>".join(text_parts))
        
        trace = {
            'type': 'scattermapbox',
            'lat': lats,
            'lon': lons,
            'mode': 'markers',
            'marker': {
                'size': 12,
                'color': self.colors['primary'],
                'opacity': 0.8
            },
            'text': hover_texts,
            'hoverinfo': 'text'
        }
        
        # Calculate center of map
        center_lat = sum(lats) / len(lats) if lats else 39.0997
        center_lon = sum(lons) / len(lons) if lons else -94.5786
        
        layout = {
            'title': chart_config.get('title', 'Vehicle Locations'),
            'mapbox': {
                'style': 'open-street-map',
                'center': {'lat': center_lat, 'lon': center_lon},
                'zoom': 11
            },
            'hovermode': 'closest',
            'margin': {'l': 0, 'r': 0, 't': 40, 'b': 0},
            'font': {
                'family': 'Inter, system-ui, sans-serif',
                'size': 12,
                'color': '#1f2937'
            }
        }
        
        return {
            'data': [trace],
            'layout': layout,
            'config': {
                'responsive': True,
                'displayModeBar': True,
                'displaylogo': False
            }
        }
    
    def _generate_metric_card(
        self, 
        chart_config: Dict[str, Any], 
        results: List[Dict[str, Any]], 
        columns: List[str]
    ) -> Dict[str, Any]:
        """Generate metric card for single value."""
        value_column = chart_config.get('value_column') or chart_config.get('y_columns', [columns[0]])[0]
        value = results[0].get(value_column) if results else 0
        
        # Format value
        if isinstance(value, float):
            formatted_value = f"{value:,.2f}"
        elif isinstance(value, int):
            formatted_value = f"{value:,}"
        else:
            formatted_value = str(value)
        
        return {
            'type': 'metric',
            'value': formatted_value,
            'label': chart_config.get('title') or self._format_label(value_column),
            'raw_value': value
        }
    
    def _generate_table(
        self, 
        chart_config: Dict[str, Any], 
        results: List[Dict[str, Any]], 
        columns: List[str]
    ) -> Dict[str, Any]:
        """Generate table for detailed data."""
        # Format headers
        headers = [self._format_label(col) for col in columns]
        
        # Extract cell values
        cells = []
        for col in columns:
            column_values = []
            for row in results:
                value = row.get(col)
                # Format value
                if isinstance(value, float):
                    column_values.append(f"{value:,.2f}")
                elif isinstance(value, int):
                    column_values.append(f"{value:,}")
                elif value is None:
                    column_values.append("-")
                else:
                    column_values.append(str(value))
            cells.append(column_values)
        
        trace = {
            'type': 'table',
            'header': {
                'values': headers,
                'fill': {'color': '#f3f4f6'},
                'align': 'left',
                'font': {
                    'family': 'Inter, system-ui, sans-serif',
                    'size': 12,
                    'color': '#1f2937'
                },
                'height': 40
            },
            'cells': {
                'values': cells,
                'fill': {'color': '#ffffff'},
                'align': 'left',
                'font': {
                    'family': 'Inter, system-ui, sans-serif',
                    'size': 11,
                    'color': '#374151'
                },
                'height': 30
            }
        }
        
        layout = {
            'title': chart_config.get('title', 'Data Table'),
            'margin': {'l': 20, 'r': 20, 't': 60, 'b': 20},
            'font': {
                'family': 'Inter, system-ui, sans-serif',
                'size': 12,
                'color': '#1f2937'
            }
        }
        
        return {
            'data': [trace],
            'layout': layout,
            'config': {
                'responsive': True,
                'displayModeBar': False,
                'displaylogo': False
            }
        }
    
    def _format_label(self, text: str) -> str:
        """Convert column name to readable label."""
        # Replace underscores with spaces
        formatted = text.replace('_', ' ')
        # Capitalize words
        formatted = ' '.join(word.capitalize() for word in formatted.split())
        return formatted
    
    def _find_column(self, columns: List[str], keywords: List[str]) -> Optional[str]:
        """Find column matching keywords."""
        for col in columns:
            if any(keyword in col.lower() for keyword in keywords):
                return col
        return None


# Convenience function
def generate_plotly_chart(
    chart_config: Dict[str, Any], 
    results: List[Dict[str, Any]], 
    columns: List[str]
) -> Dict[str, Any]:
    """
    Generate Plotly chart specification.
    
    Args:
        chart_config: Chart configuration from AI
        results: Query results
        columns: Column names
        
    Returns:
        Plotly JSON specification
    """
    generator = PlotlyGenerator()
    return generator.generate(chart_config, results, columns)
