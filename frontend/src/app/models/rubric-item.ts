export interface RubricItem {
    id: string;
    label: string;
    description: string;
    max_points: number;
    type: string;
    items?: string[];
  }