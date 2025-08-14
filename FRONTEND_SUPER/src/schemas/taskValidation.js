import * as yup from "yup";

// Helper function to get the start of today (without time component)
const getStartOfToday = () => {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return today;
};

export const taskSchema = yup.object().shape({
  title: yup
    .string()
    .min(3, "Title must be at least 3 characters")
    .max(100, "Title must be less than 100 characters")
    .required("Title is required"),
  description: yup
    .string()
    .max(500, "Description must be less than 500 characters")
    .optional(),
  dueDate: yup
    .date()
    .min(getStartOfToday(), "Due date cannot be in the past")
    .required("Due date is required"),
  weight: yup
    .number()
    .min(1, "Weight must be between 1 and 5")
    .max(5, "Weight must be between 1 and 5")
    .required("Weight is required"),
  parentTaskId: yup
    .string()
    .nullable()
    .optional(),
});

export const subtaskSchema = yup.object().shape({
  title: yup
    .string()
    .min(3, "Title must be at least 3 characters")
    .max(100, "Title must be less than 100 characters")
    .required("Title is required"),
  description: yup
    .string()
    .max(500, "Description must be less than 500 characters")
    .optional(),
  dueDate: yup
    .date()
    .min(getStartOfToday(), "Due date cannot be in the past")
    .required("Due date is required"),
  weight: yup
    .number()
    .min(1, "Weight must be between 1 and 5")
    .max(5, "Weight must be between 1 and 5")
    .required("Weight is required"),
  parentTaskId: yup
    .string()
    .required("Parent task is required"),
});
