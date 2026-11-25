/*
 * Copyright (c) 2026 Jackson Haley
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_lungmen_gov_tt8_cpu (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

  wire [7:0] register_data;
  wire       zero_flag;
  wire       halted;

  tiny8_cpu core (
      .clk          (clk),
      .rst_n        (rst_n),
      .enable       (ena),
      .data_in      (ui_in),
      .program_write(uio_in[0]),
      .start        (uio_in[1]),
      .step         (uio_in[2]),
      .run          (uio_in[3]),
      .register_sel (uio_in[5:4]),
      .register_data(register_data),
      .zero_flag    (zero_flag),
      .halted       (halted)
  );

  assign uo_out  = ena ? register_data : 8'h00;
  assign uio_out = ena ? {halted, zero_flag, 6'b000000} : 8'h00;
  assign uio_oe  = ena ? 8'b11000000 : 8'h00;

  wire _unused = &{uio_in[7:6], 1'b0};

endmodule

`default_nettype none
