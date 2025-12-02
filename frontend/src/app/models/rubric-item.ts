export interface RubricItem {
  id: string;

  // Display name
  label: string;              // e.g. "Syntax"
  
  // Description text
  description?: string;

  // Maximum points assigned
  max_points: number;

  // Optional list of required function names
  items?: string[];

  // Optional type info
  type?: string;
}
