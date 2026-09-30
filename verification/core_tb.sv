`timescale 1ns/1ps
module core_tb;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,recover=0,in_valid=0,frame_ok=1,terminal_valid=0,out_ready=1;
 reg [63:0] in_seq=1,cfg_limit=16,terminal_id=0;
 reg [15:0] in_instrument=0;
 reg [31:0] in_price=100,in_qty=1,in_epoch=1,cfg_rate_limit=16;
 wire in_ready,out_valid,hold;
 wire [63:0] out_order_id,exposure,expected;
 wire [15:0] out_instrument;
 wire [31:0] out_price,out_qty;
 wire [3:0] status;
 apex_tick_core dut(.*);
 integer input_file,output_file,count,scan,ready_before;
 reg [2047:0] input_path,output_path;
 initial begin
  if(!$value$plusargs("input=%s",input_path)) $fatal(1,"missing input");
  if(!$value$plusargs("output=%s",output_path)) $fatal(1,"missing output");
  input_file=$fopen(input_path,"r");output_file=$fopen(output_path,"w");
  if(!input_file || !output_file) $fatal(1,"cannot open trace files");
  @(posedge clk);#1;reset=0;
  while(!$feof(input_file)) begin
   @(negedge clk);
   scan=$fscanf(input_file,"%d %d %d %d %d %d %d %d %d %d %d %d %d\n",recover,terminal_valid,terminal_id,in_valid,frame_ok,in_seq,in_instrument,in_price,in_qty,in_epoch,cfg_limit,cfg_rate_limit,out_ready);
   if(scan==13) begin
    #1;ready_before=in_ready;
    @(posedge clk);#1;
    $fwrite(output_file,"%0d %0d %0d %0d %0d %0d %0d %0d %0d %0d\n",ready_before,out_valid,out_valid?out_order_id:0,out_valid?out_instrument:0,out_valid?out_price:0,out_valid?out_qty:0,hold,exposure,expected,status);
   end
  end
  $fclose(input_file);$fclose(output_file);$finish;
 end
endmodule
