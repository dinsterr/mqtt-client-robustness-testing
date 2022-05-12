class SuppliedMessageGenerator:
    def __init__(self, max_number_of_messages=0):
        self.number_of_generated_messages = 0
        self.max_number_of_messages = max_number_of_messages

    def __iter__(self):
        return self

    def __next__(self):
        if self.number_of_generated_messages > self.max_number_of_messages:
            raise StopIteration

        self.number_of_generated_messages += 1
