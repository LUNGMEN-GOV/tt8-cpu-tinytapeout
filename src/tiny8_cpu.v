/*
 * Tiny8: compact 8-bit CPU for one Tiny Tapeout tile.
 * Instruction: [7:4] opcode, [3:2] destination, [1:0] source.
 * LDI consumes the next byte. Branch targets are absolute 4-bit addresses.
 */

`default_nettype none

module tiny8_cpu (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       enable,
    input  wire [7:0] data_in,
    input  wire       program_write,
    input  wire       start,
    input  wire       step,
    input  wire       run,
    input  wire [1:0] register_sel,
    output wire [7:0] register_data,
    output wire       zero_flag,
    output wire       halted
);

  localparam [3:0] OP_NOP  = 4'h0;
  localparam [3:0] OP_LDI  = 4'h1;
  localparam [3:0] OP_MOV  = 4'h2;
  localparam [3:0] OP_ADD  = 4'h3;
  localparam [3:0] OP_SUB  = 4'h4;
  localparam [3:0] OP_AND  = 4'h5;
  localparam [3:0] OP_OR   = 4'h6;
  localparam [3:0] OP_XOR  = 4'h7;
  localparam [3:0] OP_NOT  = 4'h8;
  localparam [3:0] OP_SHL  = 4'h9;
  localparam [3:0] OP_SHR  = 4'hA;
  localparam [3:0] OP_JMP  = 4'hB;
  localparam [3:0] OP_JZ   = 4'hC;
  localparam [3:0] OP_JNZ  = 4'hD;
  localparam [3:0] OP_IN   = 4'hE;
  localparam [3:0] OP_HALT = 4'hF;

  reg [7:0] program_memory [0:15];
  reg [7:0] registers      [0:3];
  reg [3:0] program_counter;
  reg [3:0] load_address;
  reg       flag_zero;
  reg       flag_carry;
  reg       is_halted;
  integer   i;

  wire [7:0] instruction = program_memory[program_counter];
  wire [3:0] opcode      = instruction[7:4];
  wire [1:0] destination = instruction[3:2];
  wire [1:0] source      = instruction[1:0];
  wire       execute     = (run | step) & ~is_halted;

  assign register_data = registers[register_sel];
  assign zero_flag     = flag_zero;
  assign halted        = is_halted;

  // Synchronous active-low reset. Priority: reset, load, start, execute.
  // START preserves program memory and resets only architectural state.
  always @(posedge clk) begin
    if (!rst_n) begin
      program_counter <= 4'h0;
      load_address    <= 4'h0;
      flag_zero       <= 1'b0;
      flag_carry      <= 1'b0;
      is_halted       <= 1'b1;
      for (i = 0; i < 4; i = i + 1)
        registers[i] <= 8'h00;
      for (i = 0; i < 16; i = i + 1)
        program_memory[i] <= 8'h00;
    end else if (enable) begin
      if (program_write) begin
        program_memory[load_address] <= data_in;
        load_address <= load_address + 4'h1;
      end else if (start) begin
        program_counter <= 4'h0;
        flag_zero       <= 1'b0;
        flag_carry      <= 1'b0;
        is_halted       <= 1'b0;
        for (i = 0; i < 4; i = i + 1)
          registers[i] <= 8'h00;
      end else if (execute) begin
        program_counter <= program_counter + 4'h1;
        case (opcode)
          OP_NOP: begin end
          OP_LDI: begin
            registers[destination] <= program_memory[program_counter + 4'h1];
            flag_zero <= (program_memory[program_counter + 4'h1] == 8'h00);
            flag_carry <= 1'b0;
            program_counter <= program_counter + 4'h2;
          end
          OP_MOV: begin
            registers[destination] <= registers[source];
            flag_zero <= (registers[source] == 8'h00);
            flag_carry <= 1'b0;
          end
          OP_ADD: begin
            registers[destination] <= registers[destination] + registers[source];
            flag_zero <= ((registers[destination] + registers[source]) == 8'h00);
            flag_carry <= ({1'b0, registers[destination]} +
                           {1'b0, registers[source]}) > 9'h0FF;
          end
          OP_SUB: begin
            registers[destination] <= registers[destination] - registers[source];
            flag_zero <= ((registers[destination] - registers[source]) == 8'h00);
            flag_carry <= registers[destination] >= registers[source];
          end
          OP_AND: begin
            registers[destination] <= registers[destination] & registers[source];
            flag_zero <= ((registers[destination] & registers[source]) == 8'h00);
            flag_carry <= 1'b0;
          end
          OP_OR: begin
            registers[destination] <= registers[destination] | registers[source];
            flag_zero <= ((registers[destination] | registers[source]) == 8'h00);
            flag_carry <= 1'b0;
          end
          OP_XOR: begin
            registers[destination] <= registers[destination] ^ registers[source];
            flag_zero <= ((registers[destination] ^ registers[source]) == 8'h00);
            flag_carry <= 1'b0;
          end
          OP_NOT: begin
            registers[destination] <= ~registers[destination];
            flag_zero <= (~registers[destination] == 8'h00);
            flag_carry <= 1'b0;
          end
          OP_SHL: begin
            registers[destination] <= {registers[destination][6:0], 1'b0};
            flag_zero <= ({registers[destination][6:0], 1'b0} == 8'h00);
            flag_carry <= registers[destination][7];
          end
          OP_SHR: begin
            registers[destination] <= {1'b0, registers[destination][7:1]};
            flag_zero <= ({1'b0, registers[destination][7:1]} == 8'h00);
            flag_carry <= registers[destination][0];
          end
          OP_JMP: begin
            program_counter <= instruction[3:0];
          end
          OP_JZ: begin
            if (flag_zero)
              program_counter <= instruction[3:0];
          end
          OP_JNZ: begin
            if (!flag_zero)
              program_counter <= instruction[3:0];
          end
          OP_IN: begin
            registers[destination] <= data_in;
            flag_zero <= (data_in == 8'h00);
            flag_carry <= 1'b0;
          end
          OP_HALT: begin
            is_halted <= 1'b1;
            program_counter <= program_counter;
          end
          default: begin
            is_halted <= 1'b1;
          end
        endcase
      end
    end
  end

  wire _unused = &{flag_carry, 1'b0};

endmodule

`default_nettype none
