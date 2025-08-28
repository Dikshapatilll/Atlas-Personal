import { PartNumberCategory } from './types';

export const PART_NUMBER_CATEGORIES: PartNumberCategory[] = [
  PartNumberCategory.MISSING_EXTENSION,
  PartNumberCategory.SURFACE_BODY,
  PartNumberCategory.INVALID_LENGTH,
  PartNumberCategory.NON_ENGLISH_CHARS,
];

export const CHART_COLORS: { [key in PartNumberCategory]: string } = {
    [PartNumberCategory.MISSING_EXTENSION]: '#EF4444', // red-500
    [PartNumberCategory.SURFACE_BODY]: '#F97316',    // orange-500
    [PartNumberCategory.INVALID_LENGTH]: '#8B5CF6',   // violet-500
    [PartNumberCategory.NON_ENGLISH_CHARS]: '#3B82F6',// blue-500
};