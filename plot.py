import csv
import matplotlib.pyplot as plt
import mplcursors  # Import the mplcursors library

def read_csv(file_path):
    x_data = []
    y_data = []

    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row if there is one
        for row in reader:
            try:
                x_value = float(row[0])
                y_value = float(row[1])
                
                x_data.append(x_value)
                y_data.append(y_value)
            except ValueError:
                print(f"Skipping row due to conversion error: {row}")

    return x_data, y_data

def plot_scatter(x_data, y_data):
    plt.figure(figsize=(10, 6))
    
    scatter = plt.scatter(x_data, y_data, color='blue', marker='o', edgecolor='black')
    
    plt.xlabel('X Data')
    plt.ylabel('Y Data')
    plt.title('Scatter Plot of X vs Y')
    plt.grid(True)
    plt.tight_layout()

    # Add interactive cursor with hover functionality
    cursor = mplcursors.cursor(scatter, hover=True)
    
    # Show annotation on hover and remove it when cursor is moved away
    @cursor.connect("add")
    def on_add(sel):
        sel.annotation.set_text(f'({sel.target[0]:.2f}, {sel.target[1]:.2f})')
        sel.annotation.get_bbox_patch().set_alpha(0.9)  # Set annotation opacity
        sel.annotation.draggable(False)  # Prevent dragging

    # Connect a handler to remove the annotation when moving the cursor away
    @cursor.connect("remove")
    def on_remove(sel):
        sel.annotation.set_visible(False)  # Hide the annotation
        plt.draw()  # Update the plot to reflect the changes

    plt.show()

def main():
    file_path = '/home/josten/Desktop/Intern/DataLog6.csv'  # Update this to your CSV file path
    x_data, y_data = read_csv(file_path)
    plot_scatter(x_data, y_data)

if __name__ == "__main__":
    main()
