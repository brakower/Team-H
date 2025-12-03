export interface RubricItem {
  id: string;

  // Display name
  title: string;              // e.g. "Syntax"
  
  // Description text
  description?: string;

  // Maximum points assigned
  max_points: number;

  // Optional type info
  type?: string;

  items?: string[];
}


